"""RAG 单智能体聊天服务 (流式编排).

仅负责把各子模块拼成 SSE 事件流, 具体逻辑在:
  - app.rag.retrieval              知识库检索 + context 拼接 (中性原语层)
  - app.services.rag.web_context   联网搜索 + 安全过滤
  - app.services.rag.memory        query 改写 + 历史压缩
  - app.runtime.agent_harness      Prompt / 轮次 / 降级策略
  - app.services.rag.message_utils 消息格式化辅助
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from loguru import logger

from app.runtime.stream_sink import set_sink
from app.config import settings
from app.core.web_search import get_provider as get_web_search_provider
from app.core.llm import get_chat_llm
from app.runtime.agent_harness import HarnessUsageStats, get_agent_harness
from app.runtime.tool_runner import run_parallel_agent
import app.services.chat_memory as chat_memory
from app.services.rag.memory import compact_if_needed, rewrite_question
from app.rag.retrieval import build_context
from app.services.rag.message_utils import content_to_text, history_to_messages
from app.services.rag.web_context import build_web_context
from app.tools.mcp_loader import get_all_tools
from app.tools.meta import get_meta


# RAG chat 不应该让 LLM 调诊断专用工具 / 写工具 / 元工具,
# 只暴露"看一眼系统状态"这种纯只读 + 用户可理解的工具.
_RAG_TOOL_EXCLUDE = {
    "search_knowledge_base",  # 已经在前置 retrieve 阶段做了, 不让 LLM 重复调
    "web_search",             # 联网走前端开关, 不让 LLM 自己决定 (避免乱搜)
    "get_current_time",       # 没必要
    "mcp_search_tools",       # Lazy MCP 元工具
    "mcp_execute_tool",
    "delegate_to_evidence_collector",   # 诊断专用 subagent
    "delegate_to_kb_researcher",
    "delegate_to_report_writer",
}


def _select_rag_tools() -> list:
    """挑出 RAG chat 可用的只读 MCP 工具."""
    try:
        all_tools = get_all_tools()
    except Exception as exc:
        logger.warning(f"[rag] get_all_tools 失败, 退化为无工具模式: {type(exc).__name__}: {exc}")
        return []
    selected = [
        t for t in all_tools
        if get_meta(t.name).read_only and t.name not in _RAG_TOOL_EXCLUDE
    ]
    return selected


def _supports_thinking(model_name: str) -> bool:
    name = (model_name or "").lower()
    return any(tag in name for tag in ("qwen3", "qwen-plus", "qwen-max-latest", "qwq", "qvq"))


async def stream_chat(
    question: str,
    *,
    session_id: str = "default",
    top_k: int | None = None,
    web_search: bool = False,
    mcp_tools: bool = True,
) -> AsyncIterator[dict]:
    """流式 RAG 聊天, yield 一系列事件:
      - progress : 阶段提示 (改写 / 检索 / 联网 / LLM 启动 / 统计)
      - thinking : 推理链 token (qwen3 等支持思考的模型)
      - token    : LLM 输出 token
      - error    : 异常
    """
    effective_top_k = max(1, int(top_k or settings.rag_top_k))
    retrieval_data = {
        "top_k": effective_top_k,
        "candidate_k": settings.rag_retrieve_k,
        "use_hybrid": settings.rag_hybrid_enabled,
        "use_rerank": settings.rag_rerank_enabled,
    }
    logger.info(
        f"[rag] session={session_id} | question={question[:80]}... | "
        f"top_k={effective_top_k} | candidate_k={settings.rag_retrieve_k} | "
        f"web_search={web_search} | mcp_tools={mcp_tools}"
    )

    total_t0 = time.perf_counter()
    t0 = total_t0

    def progress(
        stage: str,
        label: str,
        detail: str = "",
        *,
        mark_start: bool = False,
        data: dict | None = None,
    ) -> dict:
        nonlocal t0
        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        if mark_start:
            t0 = time.perf_counter()
        return {
            "type": "progress",
            "stage": stage,
            "label": label,
            "detail": detail,
            "elapsed_ms": elapsed_ms,
            "data": data or {},
        }

    session = await chat_memory.load_session(session_id)
    summary = session.get("summary") or "(无)"
    recent_messages = session.get("recent_messages") or []

    # ---------- Stage 1: Query rewrite ----------
    need_rewrite = bool(
        settings.rag_chat_memory_enabled
        and settings.rag_chat_rewrite_enabled
        and (recent_messages or (session.get("summary") or ""))
    )
    if need_rewrite:
        yield progress("rewrite", "正在改写查询", "融合历史上下文与指代补全", mark_start=True)
    rewritten_question = await rewrite_question(
        question,
        summary=session.get("summary") or "",
        recent_messages=recent_messages,
    )
    if need_rewrite:
        rewrite_data = {"original": question, "rewritten": rewritten_question}
        if rewritten_question != question:
            yield progress(
                "rewrite_done", "查询已改写", rewritten_question[:80],
                mark_start=True, data=rewrite_data,
            )
        else:
            yield progress(
                "rewrite_done", "查询无需改写", "",
                mark_start=True, data=rewrite_data,
            )

    # ---------- Stage 2: retrieve + web_search 并行 ----------
    pipeline_text = "Hybrid BM25+RRF" if settings.rag_hybrid_enabled else "Vector Only"
    if settings.rag_rerank_enabled:
        pipeline_text += " -> Rerank"
    yield progress(
        "retrieve", "正在检索知识库",
        f"top_k={effective_top_k} · candidate_k={settings.rag_retrieve_k} · {pipeline_text}",
        mark_start=True,
        data=retrieval_data | {"pipeline": pipeline_text},
    )
    if web_search:
        yield progress("web", "正在联网补充资料", "", data={"provider": get_web_search_provider()})

    retrieve_task = asyncio.create_task(
        build_context(rewritten_question, top_k=effective_top_k)
    )
    web_task = asyncio.create_task(
        build_web_context(
            rewritten_question,
            summary=session.get("summary") or "",
            recent_messages=recent_messages,
            enabled=web_search,
        )
    )
    try:
        context, hits, sources, hits_meta = await retrieve_task
    except Exception as exc:
        logger.exception(f"[rag] 知识库检索失败, 启用降级: {exc}")
        fallback = get_agent_harness().rag_fallback(stage="retrieve", exc=exc)
        context = fallback["context"]
        hits = 0
        sources = fallback["sources"]
        hits_meta = fallback["hits_meta"]
        yield progress(
            "retrieve_degraded", "知识库检索降级", fallback["event_data"]["error_type"],
            mark_start=True, data=fallback["event_data"],
        )
    if hits:
        src_preview = ", ".join(dict.fromkeys(sources[:3])) if sources else ""
        yield progress(
            "retrieve_done", f"检索完成, 命中 {hits} 个片段", src_preview,
            mark_start=True,
            data=retrieval_data | {"hits": hits_meta, "pipeline": pipeline_text},
        )
    else:
        yield progress(
            "retrieve_done", "知识库未命中相关内容", "",
            mark_start=True,
            data=retrieval_data | {"hits": [], "pipeline": pipeline_text},
        )

    try:
        web_context, web_sources, web_hits, web_skip_reason = await web_task
    except Exception as exc:
        logger.exception(f"[rag] 联网补充失败, 启用降级: {exc}")
        fallback = get_agent_harness().web_fallback(stage="web", exc=exc)
        web_context = fallback["context"]
        web_sources = fallback["sources"]
        web_hits = fallback["hits"]
        web_skip_reason = fallback["skip_reason"]
        if web_search:
            yield progress(
                "web_degraded", "联网补充降级", fallback["event_data"]["error_type"],
                mark_start=True, data=fallback["event_data"],
            )
    if web_search:
        if web_hits:
            yield progress(
                "web_done", f"联网补充完成 ({len(web_hits)} 条)",
                ", ".join(h.get("title", "")[:30] for h in web_hits[:2]),
                mark_start=True,
                data={
                    "results": web_hits,
                    "topics": [s.replace("web:", "") for s in web_sources],
                    "provider": get_web_search_provider(),
                },
            )
        else:
            yield progress(
                "web_done", "联网搜索已跳过", web_skip_reason or "未触发联网",
                mark_start=True,
                data={"results": [], "skip_reason": web_skip_reason},
            )

    logger.info(
        f"[rag] 检索命中 {hits} 篇 "
        f"(hybrid={settings.rag_hybrid_enabled}, rerank={settings.rag_rerank_enabled})"
    )

    # ---------- 注入最近 AIOps 诊断报告 (跨 session, 走 Redis) ----------
    # 不依赖联网开关, 让 "刚才那个 vmmem 是什么" 这种指代追问也能找到答案.
    # 只取 1 份, 单份截断 1200 字 (报告头 TL;DR 已足够); 想看更早请去 AIOps 页面.
    try:
        recent_reports = await chat_memory.get_recent_diagnosis_reports(limit=1)
    except Exception as e:
        logger.warning(f"[rag] 读取最近诊断报告失败: {type(e).__name__}: {e}")
        recent_reports = []
    if recent_reports:
        diagnosis_context = "\n\n---\n\n".join(
            f"[诊断 @ {r.get('ts', '')}]\n{(r.get('report') or '')[:1200]}"
            for r in recent_reports
        )
    else:
        diagnosis_context = "(暂无最近诊断报告)"

    harness = get_agent_harness()
    user_prompt = harness.build_rag_user_prompt(
        summary=summary,
        diagnosis_context=diagnosis_context,
        context=context,
        web_context=web_context,
        question=question,
    )

    # ---------- Stage 3: 工具回合 + 流式 LLM ----------
    rag_tools = _select_rag_tools() if mcp_tools else []
    tools_enabled = bool(rag_tools)
    yield progress(
        "llm_start",
        "模型正在生成回答" + (f" · 启用 {len(rag_tools)} 个只读工具" if tools_enabled else ""),
        "",
        mark_start=True,
        data={
            "model": harness.rag_chat_model(),
            "tools_enabled": tools_enabled,
            "tools": [t.name for t in rag_tools] if tools_enabled else [],
        },
    )
    llm_kwargs: dict[str, Any] = {"temperature": 0.3, "streaming": True}
    if _supports_thinking(harness.rag_chat_model()):
        llm_kwargs["extra_body"] = {"enable_thinking": True}
    llm = get_chat_llm(model=harness.rag_chat_model(), **llm_kwargs)

    full_answer = ""
    input_tokens = output_tokens = total_tokens = 0
    tool_calls_count = tool_ms = 0
    llm_t0 = time.perf_counter()

    if tools_enabled:
        # ===== 工具增强路径: run_parallel_agent + stream_sink 旁路 =====
        # LLM 自己决定调不调工具; 不调就 1 轮直接出答案, 调了就 2-3 轮.
        # ContextVar set 在当前 task, asyncio.create_task 自动复制 context,
        # 所以 tool_runner 内部 emit() 拿得到这个 sink_q.
        sink_q: asyncio.Queue[dict] = asyncio.Queue(maxsize=2048)
        set_sink(sink_q)
        sentinel = object()

        # 用 (role, content) 复用 run_parallel_agent 的输入约定. system 由它自动 prepend.
        history_msgs: list[tuple[str, str]] = []
        for m in history_to_messages(recent_messages):
            role = "user" if isinstance(m, HumanMessage) else "assistant"
            history_msgs.append((role, content_to_text(m.content)))
        history_msgs.append(("user", user_prompt))

        async def _runner() -> dict:
            try:
                policy = harness.rag_tool_policy()
                return await run_parallel_agent(
                    llm=llm,
                    tools=rag_tools,
                    system_prompt=harness.rag_system_prompt(tools_enabled=True),
                    inputs={"messages": history_msgs},
                    max_iters=policy.max_iters,
                    max_parallel=policy.max_parallel,
                )
            finally:
                # 不论成功失败, 通知主循环退出消费
                try:
                    sink_q.put_nowait({"__sentinel__": sentinel})
                except asyncio.QueueFull:
                    pass

        runner_task = asyncio.create_task(_runner())
        try:
            while True:
                ev = await sink_q.get()
                if ev.get("__sentinel__") is sentinel:
                    break
                etype = ev.get("type")
                if etype == "step_token":
                    content = ev.get("content", "")
                    if content:
                        full_answer += content
                        yield {"type": "token", "content": content}
                elif etype == "tool_call":
                    tool_calls_count += 1
                    name = ev.get("name") or "?"
                    elapsed_ms = int(ev.get("elapsed_ms") or 0)
                    tool_ms += elapsed_ms
                    status = ev.get("status") or "?"
                    yield {
                        "type": "progress",
                        "stage": "tool_call",
                        "label": f"调用工具 {name}",
                        "detail": f"{elapsed_ms}ms · {status}",
                        "elapsed_ms": elapsed_ms,
                        "data": {
                            "name": name,
                            "elapsed_ms": elapsed_ms,
                            "status": status,
                            "result_chars": ev.get("result_chars"),
                            "read_only": ev.get("read_only", True),
                        },
                    }
                elif etype == "usage":
                    input_tokens  += int(ev.get("input_tokens")  or 0)
                    output_tokens += int(ev.get("output_tokens") or 0)
                    total_tokens  += int(ev.get("total_tokens")  or 0)
                # 其他事件 (step_start 等) 直接忽略, 不让 RAG chat 看到诊断专用字段

            # runner 完成, 拿 result 做兜底
            try:
                result = await runner_task
            except Exception as exc:
                logger.exception(f"[rag] tool runner 异常: {exc}")
                yield {"type": "error", "message": f"工具回合失败: {type(exc).__name__}: {exc}"}
                return

            # 流式 fallback (run_parallel_agent 内部 astream 抛错回退到 ainvoke) 时,
            # step_token 没 emit, 但最终 AIMessage.content 完整, 一次性补一段 token.
            last_msg = result.get("messages", [])
            answer_from_result = ""
            if last_msg:
                tail = last_msg[-1]
                answer_from_result = content_to_text(getattr(tail, "content", "")) or ""
            if not full_answer and answer_from_result:
                full_answer = answer_from_result
                yield {"type": "token", "content": answer_from_result}
            elif not full_answer and not answer_from_result:
                # LLM 全程只调工具不出文字, 给个保底说明
                fallback = "已调用工具采集实时数据, 但模型未给出文字总结. 请在后续问题里要求'综合上面工具结果给我一段总结'."
                full_answer = fallback
                yield {"type": "token", "content": fallback}
        except Exception as exc:
            logger.exception(f"[rag] 工具回合主循环异常: {exc}")
            if not runner_task.done():
                runner_task.cancel()
            yield {"type": "error", "message": f"工具回合失败: {type(exc).__name__}: {exc}"}
            return

        if total_tokens == 0:
            total_tokens = input_tokens + output_tokens
    else:
        # ===== 退化路径: 没有 MCP 工具时仍按原来方式纯流式 =====
        messages = [
            SystemMessage(content=harness.rag_system_prompt(tools_enabled=False)),
            *history_to_messages(recent_messages),
            HumanMessage(content=user_prompt),
        ]
        try:
            async for chunk in llm.astream(messages):
                ak = getattr(chunk, "additional_kwargs", None)
                reasoning = ak.get("reasoning_content") if isinstance(ak, dict) else None
                if reasoning:
                    yield {"type": "thinking", "content": reasoning}
                content = content_to_text(chunk.content)
                if content:
                    full_answer += content
                    yield {"type": "token", "content": content}
                um = getattr(chunk, "usage_metadata", None)
                if um:
                    input_tokens  = max(input_tokens,  int(um.get("input_tokens")  or 0))
                    output_tokens = max(output_tokens, int(um.get("output_tokens") or 0))
                    total_tokens  = max(total_tokens,  int(um.get("total_tokens")  or 0))
            if total_tokens == 0:
                total_tokens = input_tokens + output_tokens
        except Exception as e:
            logger.exception(f"[rag] LLM 调用失败: {e}")
            yield {"type": "error", "message": f"LLM 调用失败: {type(e).__name__}: {e}"}
            return

    # ---------- 收尾: 写 memory + 输出 stats ----------
    try:
        await chat_memory.append_message(
            session_id, role="user", content=question, rewritten_query=rewritten_question,
        )
        await chat_memory.append_message(
            session_id, role="assistant", content=full_answer,
            sources=sources + web_sources,
        )
        await compact_if_needed(session_id)
    except Exception as exc:
        logger.warning(f"[rag] memory 写入失败: {type(exc).__name__}: {exc}")

    llm_ms = int((time.perf_counter() - llm_t0) * 1000)
    total_ms = int((time.perf_counter() - total_t0) * 1000)
    usage_stats = HarnessUsageStats(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        llm_ms=llm_ms,
        total_ms=total_ms,
        tool_calls=tool_calls_count,
        tool_ms=tool_ms,
        answer_chars=len(full_answer),
        model=harness.rag_chat_model(),
        run_kind="rag_chat",
    )
    budget_event = harness.build_budget_event(harness.evaluate_budget(usage_stats))
    if budget_event:
        yield budget_event
    stats_event = harness.build_usage_stats_event(usage_stats)
    stats_event["data"]["tools_enabled"] = tools_enabled
    yield stats_event
