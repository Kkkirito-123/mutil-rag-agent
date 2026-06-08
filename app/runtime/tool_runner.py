"""带 read-only 并行编排的轻量 ReAct 执行器.

替代 langchain.agents.create_agent, 因为后者默认串行执行 tool_calls.
保持与 create_agent 相同的对外契约: ainvoke({"messages": [...]}) -> {"messages": [...]}

设计要点 (§3 cc-haha 借鉴):
  - 一次 LLM round 可能产生多个 tool_calls (并行查询 metrics+logs+rag 等)
  - 用 ToolMeta.concurrency_safe 把 tool_calls 切成"批": 相邻的 safe call 合一批 gather()
  - 顺序仍然受保护: 写工具会切批, 写之前的读全并行, 写之后的读再开新一批
  - fail-isolation: 同批一个工具失败不影响兄弟工具结果
  - max_result_chars 自动截断, 防止 20KB 日志直接喂回 LLM 导致 context 爆炸
  - max_iters 硬上限, 防止 LLM 死循环调用工具

参考:
  cc-haha src/services/tools/toolOrchestration.ts:partitionToolCalls
  CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY (cc-haha 默认 10, 这里取 6 更保守)
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from loguru import logger

from app.runtime.stream_sink import emit as emit_stream
from app.tools.meta import get_meta


# ============================================================
# 常量
# ============================================================
DEFAULT_MAX_ITERS = 6      # LLM <-> tool 往返上限 (防死循环)
DEFAULT_MAX_PARALLEL = 6   # 单批并发上限 (cc-haha 默认 10, OnCall 保守取 6)


# ============================================================
# 工具调用规范化
# ============================================================
def _normalize_tool_call(tc: Any) -> Optional[Dict[str, Any]]:
    """LangChain v1 中 tool_calls 既可能是 dict 也可能是 ToolCall TypedDict, 统一成 dict.

    返回结构:
        {"id": str, "name": str, "args": dict}
    任一字段缺失时返回 None (跳过).
    """
    if isinstance(tc, dict):
        tid = tc.get("id") or tc.get("tool_call_id")
        name = tc.get("name")
        args = tc.get("args") or tc.get("arguments") or {}
    else:
        tid = getattr(tc, "id", None)
        name = getattr(tc, "name", None)
        args = getattr(tc, "args", None) or getattr(tc, "arguments", None) or {}

    if not name or not tid:
        return None
    if not isinstance(args, dict):
        # 偶尔模型返回 JSON 字符串, 容错一下
        try:
            import json
            args = json.loads(args) if isinstance(args, str) else {}
        except Exception:
            args = {}
    return {"id": tid, "name": name, "args": args}


# ============================================================
# 分批 (partition)
# ============================================================
def partition_tool_calls(
    tool_calls: Sequence[Dict[str, Any]],
    max_parallel: int = DEFAULT_MAX_PARALLEL,
) -> List[Tuple[bool, List[Dict[str, Any]]]]:
    """把 tool_calls 切成批, 每批要么全 concurrency_safe (并行), 要么单工具 (串行).

    规则:
      - 相邻 safe 工具合并到同一批, 直到 batch 达到 max_parallel
      - 遇到 unsafe 工具, 立即新开一批, 该批只放它自己 (并标记 is_safe=False)
      - 未在 TOOL_META 登记的工具 → get_meta() 返回保守默认 → concurrency_safe=False, 单批

    Args:
        tool_calls: 已规范化的 tool_call 列表
        max_parallel: 单批最大并发数

    Returns:
        [(is_safe, [tc, tc, ...]), (is_safe, [tc]), ...]
        is_safe=True 时调用方应 asyncio.gather; False 时应串行执行.
    """
    batches: List[Tuple[bool, List[Dict[str, Any]]]] = []
    for tc in tool_calls:
        meta = get_meta(tc["name"])
        is_safe = meta.concurrency_safe
        if (
            batches
            and batches[-1][0]  # 上一批是 safe
            and is_safe
            and len(batches[-1][1]) < max_parallel
        ):
            batches[-1][1].append(tc)
        else:
            batches.append((is_safe, [tc]))
    return batches


# ============================================================
# 单工具执行 (含截断 + 异常隔离)
# ============================================================
async def _invoke_tool(tool: BaseTool, args: Dict[str, Any]) -> str:
    """统一调用接口: 优先 ainvoke (异步), 回退 invoke (同步)."""
    if hasattr(tool, "ainvoke"):
        result = await tool.ainvoke(args)
    else:
        result = tool.invoke(args)
    return result if isinstance(result, str) else str(result)


async def _safe_invoke_tool(
    tool: BaseTool,
    tool_call: Dict[str, Any],
) -> ToolMessage:
    """异常隔离 + 结果截断, 返回标准化 ToolMessage.

    - 工具抛错 → 转成 "[执行失败: ...]" 字符串, 不让 gather 整批挂掉
    - 结果超长 → 按 ToolMeta.max_result_chars 截断
    """
    name = tool_call["name"]
    meta = get_meta(name)
    started = time.perf_counter()

    try:
        content = await _invoke_tool(tool, tool_call["args"])
    except Exception as exc:
        logger.warning(f"[ParallelAgent] tool {name!r} 执行失败: {type(exc).__name__}: {exc}")
        content = f"[执行失败: {type(exc).__name__}: {exc}]"

    elapsed_ms = (time.perf_counter() - started) * 1000

    # 结果截断 (cc-haha maxResultSizeChars 同款)
    if meta.max_result_chars and len(content) > meta.max_result_chars:
        truncated_len = len(content)
        content = (
            content[: meta.max_result_chars]
            + f"\n[truncated: original {truncated_len} chars, kept first {meta.max_result_chars}]"
        )
        logger.debug(
            f"[ParallelAgent] tool {name!r} 输出 {truncated_len} 字符, 截断到 {meta.max_result_chars}"
        )

    logger.info(
        f"[ParallelAgent] tool={name} "
        f"safe={meta.concurrency_safe} read_only={meta.read_only} "
        f"elapsed={elapsed_ms:.0f}ms result_chars={len(content)}"
    )
    # 把工具调用事件旁路给 diagnosis_runner, 前端监控和 Worker 审计都能消费.
    await emit_stream({
        "type": "tool_call",
        "name": name,
        "elapsed_ms": int(elapsed_ms),
        "read_only": bool(meta.read_only),
        "result_chars": len(content),
        "status": "failed" if content.startswith("[执行失败") else "ok",
    })

    return ToolMessage(content=content, tool_call_id=tool_call["id"], name=name)


# ============================================================
# 审批侧 helper: 给前端审批卡看 "这次要干什么"
# ============================================================
def _impact_summary_for(tool_name: str, tool_args: Dict[str, Any]) -> str:
    """根据 ToolMeta + 入参猜一句"影响范围"提示, 让审批人不用看 args 也能看明白.

    保守: 拿不到 meta / 入参为空就降级成空字符串, 前端会画"无影响说明".
    """
    try:
        from app.tools.meta import get_meta
        meta = get_meta(tool_name)
        risk = getattr(meta, "risk_level", "low")
        side = getattr(meta, "side_effect", "none")
        destructive = bool(getattr(meta, "destructive", False))
        bits = [f"风险等级 {risk}", f"副作用 {side}"]
        if destructive:
            bits.append("不可逆")
        if getattr(meta, "is_notification", False):
            bits.append("外发通知")
        if tool_args:
            preview_keys = list(tool_args.keys())[:3]
            bits.append("入参 keys: " + ", ".join(preview_keys))
        return " · ".join(bits)
    except Exception:
        return ""


# ============================================================
# 主入口
# ============================================================
async def run_parallel_agent(
    *,
    llm: BaseChatModel,
    tools: Sequence[BaseTool],
    system_prompt: str,
    inputs: Dict[str, Any],
    max_iters: int = DEFAULT_MAX_ITERS,
    max_parallel: int = DEFAULT_MAX_PARALLEL,
    decisions: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """带 read-only 并行的 ReAct 风格执行器.

    与 langchain.agents.create_agent.ainvoke({"messages": [...]}) 兼容:
      - 输入: {"messages": [...]}  (单条 user message 或多条历史)
      - 输出: {"messages": [...]}  (system + user + 多轮 ai/tool)

    Args:
        llm: 已配置的 BaseChatModel (会在内部 bind_tools)
        tools: 已通过 Harness 过滤的工具集 (allow + ask)
        system_prompt: 系统提示
        inputs: {"messages": [...]} 兼容 create_agent 输入
        max_iters: LLM <-> tool 往返上限
        max_parallel: 单批 gather 并发上限
        decisions: §1 PermissionMode 决策 dict (tool_name -> PermissionDecision).
                   - allow → 直接调用
                   - ask   → MVP 阶段直接转 deny (打印 reason)
                   - deny  → 不应该出现在这里 (Harness 已过滤掉)
                   None → 跳过权限检查 (向后兼容老代码 / 单测)

    Returns:
        {"messages": [完整对话历史]}
    """
    if not tools:
        raise ValueError("[ParallelAgent] tools 不能为空")
    decisions = decisions or {}

    tools_by_name: Dict[str, BaseTool] = {t.name: t for t in tools}
    bound_llm = llm.bind_tools(list(tools))

    # ===== 组装初始 messages =====
    raw_msgs = inputs.get("messages") or []
    messages: List[BaseMessage] = [SystemMessage(content=system_prompt)]
    for m in raw_msgs:
        if isinstance(m, BaseMessage):
            messages.append(m)
        elif isinstance(m, tuple) and len(m) == 2:
            role, content = m
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "system":
                # 已加过 system, 但允许多条
                messages.append(SystemMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
            else:
                messages.append(HumanMessage(content=str(content)))
        elif isinstance(m, dict):
            role = m.get("role", "user")
            content = m.get("content", "")
            cls = {"system": SystemMessage, "user": HumanMessage, "assistant": AIMessage}.get(
                role, HumanMessage
            )
            messages.append(cls(content=content))
        else:
            messages.append(HumanMessage(content=str(m)))

    # ===== ReAct loop =====
    for round_idx in range(max_iters):
        # 用 astream 替代 ainvoke, 把 token 经 emit_stream 推给 diagnosis_runner,
        # 让前端在等待期间看到模型正在生成. 工具调用的 tool_calls 也会在
        # accumulated chunk 的最后一帧给出, 和 ainvoke 等价.
        acc: Optional[AIMessage] = None
        try:
            async for chunk in bound_llm.astream(messages):
                acc = chunk if acc is None else (acc + chunk)  # type: ignore[operator]
                text = getattr(chunk, "content", "")
                if isinstance(text, list):
                    text = "".join(
                        c.get("text", "") if isinstance(c, dict) else str(c)
                        for c in text
                    )
                if text:
                    await emit_stream({"type": "step_token", "content": text})
        except Exception:
            # 流式失败, 回退到一次性 ainvoke (保底, 比如 DeepSeek thinking mode 要回传 reasoning_content)
            acc = await bound_llm.ainvoke(messages)

        ai_msg = acc if isinstance(acc, AIMessage) else AIMessage(
            content=getattr(acc, "content", str(acc))
        )
        messages.append(ai_msg)

        # ===== 真实 token 统计 (DeepSeek/DashScope 都通过 stream_usage=True 在末帧给) =====
        # 失败回退的 ainvoke 也会带 usage_metadata, 一并处理. 拿不到就跳过, 不影响主流程.
        usage_meta = getattr(ai_msg, "usage_metadata", None) or {}
        resp_meta = getattr(ai_msg, "response_metadata", None) or {}
        # DeepSeek 的 prompt_cache_hit_tokens / prompt_cache_miss_tokens 在 raw token_usage 里
        raw_usage = (resp_meta.get("token_usage") if isinstance(resp_meta, dict) else None) or {}
        if usage_meta or raw_usage:
            payload = {
                "type": "usage",
                "round": round_idx + 1,
                "input_tokens": int(usage_meta.get("input_tokens") or raw_usage.get("prompt_tokens") or 0),
                "output_tokens": int(usage_meta.get("output_tokens") or raw_usage.get("completion_tokens") or 0),
                "total_tokens": int(usage_meta.get("total_tokens") or raw_usage.get("total_tokens") or 0),
            }
            # DeepSeek 缓存命中字段, 没有就置 0
            cache_hit = raw_usage.get("prompt_cache_hit_tokens")
            cache_miss = raw_usage.get("prompt_cache_miss_tokens")
            if cache_hit is not None or cache_miss is not None:
                payload["cache_hit_tokens"] = int(cache_hit or 0)
                payload["cache_miss_tokens"] = int(cache_miss or 0)
            model_name = resp_meta.get("model_name") if isinstance(resp_meta, dict) else None
            if model_name:
                payload["model"] = model_name
            await emit_stream(payload)

        raw_calls = getattr(ai_msg, "tool_calls", None) or []
        normalized = [tc for tc in (_normalize_tool_call(c) for c in raw_calls) if tc]

        if not normalized:
            logger.debug(f"[ParallelAgent] round {round_idx+1}: 无 tool_calls, 退出 loop")
            break

        # ===== 双层防御 =====
        # Layer A: 未注册工具 (Harness 应已过滤, 这里是双保险防 LLM 自由发挥)
        # Layer B: PermissionDecision 检查 (§1 PermissionMode)
        #   - allow → 进入 valid_calls
        #   - ask   → MVP 转 deny + 友好提示
        #   - deny  → 不应该出现, 因为 Harness 不会暴露 deny 工具给 LLM. 但 LLM 可能"猜"工具名
        valid_calls: List[Dict[str, Any]] = []
        invalid_results: List[ToolMessage] = []
        for tc in normalized:
            name = tc["name"]
            if name not in tools_by_name:
                logger.warning(
                    f"[ParallelAgent] LLM 试图调用未授权工具 {name!r}, 拒绝并回填错误"
                )
                invalid_results.append(
                    ToolMessage(
                        content=f"[拒绝] 工具 {name!r} 不在当前 Skill 允许的工具列表中.",
                        tool_call_id=tc["id"],
                        name=name,
                    )
                )
                continue

            d = decisions.get(name)
            if d is None or d.behavior == "allow":
                valid_calls.append(tc)
                continue

            if d.behavior == "ask":
                # 真审批闭环: 写一行 pending 到 approval_requests, 阻塞等人工 allow/deny.
                # 关掉 (settings.approvals_enabled=False) 或 Postgres 异常时降级为旧 MVP (转 deny).
                from app.config import settings as _settings  # 延迟导入避免循环

                handled = False
                if _settings.approvals_enabled:
                    try:
                        from app.runtime.approvals import approval_repository

                        impact = _impact_summary_for(name, tc.get("args") or {})
                        req_id = await approval_repository.create_request(
                            tool_name=name,
                            tool_args=tc.get("args") or {},
                            reason=d.reason,
                            impact_summary=impact,
                        )
                        await emit_stream({
                            "type": "tool_pending_approval",
                            "approval_id": req_id,
                            "tool": name,
                            "reason": d.reason,
                            "impact": impact,
                            "timeout_sec": _settings.approvals_timeout_sec,
                        })
                        logger.info(
                            f"[ParallelAgent] tool={name} ASK -> awaiting approval id={req_id} "
                            f"timeout={_settings.approvals_timeout_sec}s"
                        )
                        # 等人工审批可能很久, 期间先把分布式并发槽让出去, 避免空占名额
                        # 造成队头阻塞 (改造文档第 1 步与审批闭环的协调). 审批结束再抢回。
                        from app.core.distributed_limiter import current_slot
                        _slot = current_slot.get(None)
                        if _slot is not None:
                            with contextlib.suppress(Exception):
                                await _slot.pause()
                        try:
                            status = await approval_repository.wait_for_decision(req_id)
                        finally:
                            if _slot is not None:
                                with contextlib.suppress(Exception):
                                    await _slot.resume()
                        await emit_stream({
                            "type": "tool_approval_resolved",
                            "approval_id": req_id,
                            "tool": name,
                            "status": status,
                        })
                        if status == "approved":
                            logger.info(f"[ParallelAgent] tool={name} ASK -> approved by human, executing")
                            valid_calls.append(tc)
                            handled = True
                        else:
                            invalid_results.append(
                                ToolMessage(
                                    content=(
                                        f"[审批未通过: {status}] 工具 {name!r} 未获人工批准. "
                                        f"原因: {d.reason}. 请改用其他方案."
                                    ),
                                    tool_call_id=tc["id"],
                                    name=name,
                                )
                            )
                            handled = True
                    except Exception as exc:
                        logger.warning(
                            f"[ParallelAgent] 审批通道异常, 降级到旧 ask=deny: "
                            f"{type(exc).__name__}: {exc}"
                        )

                if not handled:
                    # 兜底: 没启用真审批, 或审批通道异常 → 旧行为
                    logger.info(
                        f"[ParallelAgent] tool={name} ASK -> deny (fallback) "
                        f"reason_type={d.reason_type}"
                    )
                    invalid_results.append(
                        ToolMessage(
                            content=(
                                f"[需人工审批 - 通道不可用] 工具 {name!r} 需要管理员确认才能调用. "
                                f"原因: {d.reason}. 请改用其他工具或简化方案."
                            ),
                            tool_call_id=tc["id"],
                            name=name,
                        )
                    )
                continue

            # behavior == "deny"
            logger.info(
                f"[ParallelAgent] tool={name} DENY reason_type={d.reason_type} reason={d.reason}"
            )
            invalid_results.append(
                ToolMessage(
                    content=f"[拒绝] {d.reason}",
                    tool_call_id=tc["id"],
                    name=name,
                )
            )

        if invalid_results:
            messages.extend(invalid_results)

        if not valid_calls:
            continue

        # ===== 分批 + 执行 =====
        batches = partition_tool_calls(valid_calls, max_parallel=max_parallel)
        logger.info(
            f"[ParallelAgent] round {round_idx+1}: {len(valid_calls)} tool_calls -> "
            f"{len(batches)} batches, "
            f"safe_batch_sizes={[len(b) for s, b in batches if s]} "
            f"serial={[b[0]['name'] for s, b in batches if not s]}"
        )

        for is_safe, batch in batches:
            if is_safe and len(batch) > 1:
                # 并行
                t0 = time.perf_counter()
                tool_msgs = await asyncio.gather(
                    *(_safe_invoke_tool(tools_by_name[tc["name"]], tc) for tc in batch),
                    return_exceptions=False,  # _safe_invoke_tool 内已捕获
                )
                elapsed_ms = (time.perf_counter() - t0) * 1000
                logger.info(
                    f"[ParallelAgent] parallel batch ({len(batch)}) done in {elapsed_ms:.0f}ms: "
                    f"{[tc['name'] for tc in batch]}"
                )
            else:
                # 串行 (单工具或 unsafe)
                tool_msgs = []
                for tc in batch:
                    tool_msgs.append(await _safe_invoke_tool(tools_by_name[tc["name"]], tc))

            messages.extend(tool_msgs)
    else:
        logger.warning(
            f"[ParallelAgent] 达到 max_iters={max_iters}, 强制退出 loop. "
            f"最后一条 AIMessage 可能仍有 pending tool_calls."
        )

    return {"messages": messages}
