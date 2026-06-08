"""共享诊断图运行器。

API 与 Worker 调用方的统一入口: fast / deep 图都从这里 astream, 输出结构化运行时事件。
本模块不知道 SSE、HTTP、Redis 队列消费或 Postgres 审计 —— 那些是 services 层 / Worker
层的事。诊断收尾时把报告 ingest 进 LLM Wiki 是唯一的副作用 (best-effort)。
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from typing import Any

from loguru import logger

from app.runtime.stream_sink import set_sink
from app.incidents.models import DiagnosisMode
from app.wiki.store import ingest_diagnosis
from app.runtime.agent_harness import HarnessUsageStats, get_agent_harness
# chat_memory 在 _cache_report 内 lazy import,避免 services -> orchestration -> services 循环。

RuntimeEvent = dict[str, Any]

_graph_plain = None
_deep_graph_plain = None


async def get_diagnosis_graph():
    """返回进程级缓存的 fast 诊断图 (懒构建)。"""
    global _graph_plain
    if _graph_plain is None:
        from app.agents import build_aiops_graph

        _graph_plain = build_aiops_graph()
    return _graph_plain


async def get_deep_diagnosis_graph():
    """返回进程级缓存的 deep 诊断图 (懒构建)。

    deep 图与 fast Plan-Execute-Replan 独立；这里只复用 runner 的事件转换、
    SSE 输出和报告收尾逻辑。
    """
    global _deep_graph_plain
    if _deep_graph_plain is None:
        from app.diagnosis_graphs import build_deep_graph

        _deep_graph_plain = build_deep_graph()
    return _deep_graph_plain


def make_event(
    event_type: str, stage: str, message: str = "", **data: Any
) -> RuntimeEvent:
    """构造统一的事件信封 (API SSE 流和 Worker 都用同一格式)。"""
    return {"type": event_type, "stage": stage, "message": message, "data": data}


def normalize_diagnosis_mode(value: str | DiagnosisMode | None) -> DiagnosisMode:
    """把外部传入的模式字符串归一化成内部 DiagnosisMode 枚举。"""
    if isinstance(value, DiagnosisMode):
        return value
    raw = str(value or DiagnosisMode.FAST.value).strip().lower()
    aliases = {
        "daily": DiagnosisMode.FAST,
        "normal": DiagnosisMode.FAST,
        "routine": DiagnosisMode.FAST,
        "fast": DiagnosisMode.FAST,
        "日常": DiagnosisMode.FAST,
        "常规": DiagnosisMode.FAST,
        "deep": DiagnosisMode.DEEP,
        "depth": DiagnosisMode.DEEP,
        "group": DiagnosisMode.DEEP,
        "深度": DiagnosisMode.DEEP,
    }
    return aliases.get(raw, DiagnosisMode.FAST)


def resolve_effective_mode(
    requested_mode: str | DiagnosisMode | None,
) -> tuple[DiagnosisMode, DiagnosisMode, bool]:
    """把请求的模式解析成"现在真能跑的模式" (受 deep_diagnosis_enabled 开关控制)。

    - fast 永远走原 Plan-Execute-Replan 图。
    - deep 在 `settings.deep_diagnosis_enabled=True` 时走独立 Deep Diagnosis 图。
    - deep 开关关闭时回落到 fast，并通过 group_agent_reserved 标记本次回落。
    """
    from app.config import settings

    requested = normalize_diagnosis_mode(requested_mode)
    if requested == DiagnosisMode.DEEP and settings.deep_diagnosis_enabled:
        # deep 真走独立 Deep Diagnosis Graph。
        return requested, DiagnosisMode.DEEP, False
    effective = DiagnosisMode.FAST
    group_agent_reserved = requested == DiagnosisMode.DEEP
    return requested, effective, group_agent_reserved


async def run_diagnosis_graph(
    query: str,
    *,
    session_id: str = "default",
    diagnosis_mode: str | DiagnosisMode = DiagnosisMode.FAST,
    cache_reports: bool = False,
    alert_signature: str = "",
) -> AsyncIterator[RuntimeEvent]:
    """跑 fast 或 deep LangGraph 诊断图, 产 SSE 事件流。

    Args:
        query: Alert text or user-described incident.
        session_id: Correlation id for logs and optional report cache.
        diagnosis_mode: Requested mode (fast / deep). Deep routes to the deep
            graph when settings.deep_diagnosis_enabled, else falls back to fast.
        cache_reports: When true, final reports are copied to short-term chat
            memory for follow-up RAG questions. Workers should keep this false.
        alert_signature: Same-incident fingerprint computed by the caller from
            the structured alert payload. Threaded into the graph state so the
            LLM Wiki recall_block can do direct-page lookup
            (services/<service>.md, patterns/<sig>.md). Manual/SSE callers leave it empty.
    """
    requested_mode, effective_mode, group_agent_reserved = resolve_effective_mode(
        diagnosis_mode
    )
    harness = get_agent_harness()
    total_t0 = time.perf_counter()
    input_tokens = output_tokens = total_tokens = 0
    tool_calls_count = tool_ms = 0

    logger.info(
        f"[DiagnosisRunner] session={session_id} | "
        f"requested_mode={requested_mode.value} | effective_mode={effective_mode.value} | "
        f"query={query[:100]}..."
    )

    yield make_event(
        "start",
        "diagnosis_init",
        message="开始故障诊断",
        query=query,
        session_id=session_id,
        requested_mode=requested_mode.value,
        effective_mode=effective_mode.value,
    )
    if effective_mode == DiagnosisMode.DEEP:
        mode_message = "深度诊断图: 多 Agent 取证与 RCA"
    elif group_agent_reserved:
        mode_message = "deep 模式已关闭, 本次回落到 fast Plan-Execute-Replan"
    else:
        mode_message = "fast 模式: Plan-Execute-Replan 诊断"
    yield make_event(
        "mode_selected",
        "diagnosis_mode",
        message=mode_message,
        requested_mode=requested_mode.value,
        effective_mode=effective_mode.value,
        group_agent_reserved=group_agent_reserved,
    )

    # 按 effective_mode 选 graph: deep 启用时走独立深度图, 否则走 fast。
    # 两套 graph 的 input shape 兼容 (都接受 input/diagnosis_mode/requested_diagnosis_mode/
    # alert_signature 这几个字段), 故 graph_input 共用同一份。
    if effective_mode == DiagnosisMode.DEEP:
        graph = await get_deep_diagnosis_graph()
    else:
        graph = await get_diagnosis_graph()
    token_queue: asyncio.Queue[RuntimeEvent] = asyncio.Queue(maxsize=2048)
    set_sink(token_queue)
    done_sentinel: RuntimeEvent = {"__done__": True}

    graph_config: dict[str, Any] = {"recursion_limit": harness.graph_recursion_limit()}
    graph_input: dict[str, Any] = {
        "input": query,
        "diagnosis_mode": effective_mode.value,
        "requested_diagnosis_mode": requested_mode.value,
        "alert_signature": alert_signature,
    }
    final_report = ""  # 经验 Wiki 写钩子用: 捕获本次诊断产出的最终报告文本

    async def _graph_runner() -> None:
        try:
            async for event in graph.astream(graph_input, config=graph_config):
                await token_queue.put({"__node__": event})
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            await token_queue.put({"__error__": exc})
        finally:
            await token_queue.put(done_sentinel)

    runner_task = asyncio.create_task(_graph_runner())

    try:
        while True:
            item = await token_queue.get()
            if item is done_sentinel:
                break
            if "__error__" in item:
                exc = item["__error__"]
                logger.exception(
                    f"[DiagnosisRunner] session={session_id} | 诊断异常: {exc}"
                )
                yield make_event(
                    "error",
                    "diagnosis_failed",
                    message=f"诊断失败: {type(exc).__name__}: {exc}",
                    error_type=type(exc).__name__,
                )
                return
            if "__node__" in item:
                event = item["__node__"]
                for node_name, node_output in event.items():
                    for transition in (node_output or {}).get("transition_history") or []:
                        yield make_event(
                            "transition",
                            transition.get("reason", "unknown"),
                            message=transition.get("detail", ""),
                            node=transition.get("node", node_name),
                            ts=transition.get("ts", ""),
                            reason=transition.get("reason", ""),
                        )
                    async for runtime_event in _convert_node_event(node_name, node_output):
                        if runtime_event.get("type") == "report":
                            report_text = (runtime_event.get("data") or {}).get("report") or ""
                            if report_text:
                                final_report = report_text
                            if cache_reports:
                                await _cache_report(session_id, runtime_event)
                        yield runtime_event
                continue

            event_type = item.get("type", "token")
            payload = {key: value for key, value in item.items() if key != "type"}
            if event_type == "usage":
                input_tokens += int(payload.get("input_tokens") or 0)
                output_tokens += int(payload.get("output_tokens") or 0)
                total_tokens += int(payload.get("total_tokens") or 0)
            elif event_type == "tool_call":
                tool_calls_count += 1
                tool_ms += int(payload.get("elapsed_ms") or 0)
            yield make_event(event_type, event_type, message="", **payload)

        total_ms = int((time.perf_counter() - total_t0) * 1000)
        if total_tokens == 0:
            total_tokens = input_tokens + output_tokens
        usage_stats = HarnessUsageStats(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            total_ms=total_ms,
            tool_calls=tool_calls_count,
            tool_ms=tool_ms,
            run_kind="aiops_diagnosis",
        )
        budget_event = harness.build_budget_event(harness.evaluate_budget(usage_stats))
        if budget_event:
            yield make_event(
                budget_event["type"],
                budget_event["stage"],
                message=budget_event.get("detail", ""),
                **(budget_event.get("data") or {}),
            )
        stats_event = harness.build_usage_stats_event(usage_stats)
        yield make_event(
            stats_event["type"],
            stats_event["stage"],
            message=stats_event.get("detail", ""),
            **(stats_event.get("data") or {}),
        )
        yield make_event("complete", "diagnosis_complete", message="诊断流程完成")

        # LLM Wiki 写钩子: 诊断产出报告后 ingest 进 wiki (LLM 合并相关页, best-effort 自吞异常)。
        # 这是 fast/deep/worker 三条路径的单一汇聚点。
        if final_report:
            await ingest_diagnosis(
                query=query,
                report_text=final_report,
                signature=alert_signature,
                session_id=session_id,
                mode=effective_mode.value,
            )

    except asyncio.CancelledError:
        logger.info(f"[DiagnosisRunner] session={session_id} | 运行取消")
        runner_task.cancel()
        raise
    except Exception as exc:
        logger.exception(f"[DiagnosisRunner] session={session_id} | 诊断异常: {exc}")
        yield make_event(
            "error",
            "diagnosis_failed",
            message=f"诊断失败: {type(exc).__name__}: {exc}",
            error_type=type(exc).__name__,
        )
    finally:
        if not runner_task.done():
            runner_task.cancel()
            try:
                await runner_task
            except (asyncio.CancelledError, Exception):
                pass


async def _cache_report(session_id: str, event: RuntimeEvent) -> None:
    report_text = (event.get("data") or {}).get("report") or ""
    if not report_text:
        return
    try:
        # lazy import: services -> orchestration 是主方向, 这里反向用 services.chat_memory
        # (短期记忆原语), 用 lazy import 让模块加载顺序不再形成循环。
        from app.services import chat_memory

        await chat_memory.append_diagnosis_report(report_text, session_id=session_id)
    except Exception as exc:
        logger.warning(
            f"[DiagnosisRunner] 诊断报告缓存失败 session={session_id}: "
            f"{type(exc).__name__}: {exc}"
        )


async def _convert_node_event(
    node_name: str, node_output: dict[str, Any]
) -> AsyncIterator[RuntimeEvent]:
    """把 LangGraph 节点输出转换成统一的 RuntimeEvent (SSE 友好)。"""
    if node_name == "skill_router":
        skill_name = node_output.get("selected_skill", "")
        reason = node_output.get("skill_reason", "")
        response = node_output.get("response", "")
        yield make_event(
            "skill_selected",
            "skill_selected",
            message=f"已选定 Skill: {skill_name}",
            skill=skill_name,
            reason=reason,
        )
        if response:
            yield make_event(
                "report",
                "report_generated",
                message="Router 已终止诊断",
                report=response,
            )

    elif node_name == "planner":
        plan = node_output.get("plan", [])
        yield make_event(
            "plan",
            "plan_created",
            message=f"诊断计划已生成, 共 {len(plan)} 步",
            plan=plan,
        )

    elif node_name == "executor":
        past = node_output.get("past_steps", [])
        iteration = node_output.get("iteration", 0)
        if past:
            step, result = past[-1]
            preview = result[:200] + ("..." if len(result) > 200 else "")
            yield make_event(
                "step_complete",
                "step_executed",
                message=f"完成第 {iteration} 步",
                iteration=iteration,
                step=step,
                result_preview=preview,
            )

    elif node_name == "replanner":
        response = node_output.get("response", "")
        new_plan = node_output.get("plan", [])
        if response:
            yield make_event(
                "report",
                "report_generated",
                message="最终诊断报告已生成",
                report=response,
            )
        elif new_plan:
            yield make_event(
                "replan",
                "plan_updated",
                message=f"调整计划, 剩余 {len(new_plan)} 步",
                plan=new_plan,
            )

    elif node_name == "fork_skill":
        response = node_output.get("response", "")
        if response:
            yield make_event(
                "report",
                "report_generated",
                message="Fork Skill 子图已产出最终报告",
                report=response,
                fork=True,
            )

    # ===== Deep Diagnosis 节点 =====
    # 节点名与 fast 互不重叠 (incident_manager/correlation_context/evidence_plan/
    # log_agent/metric_agent/infra_agent/runbook_agent/evidence_reducer/rca_judge/
    # remediation_planner/report), 故可在同一函数里分发, 不影响 fast 行为。
    # 大量事件已由 transition_history -> "transition" SSE 自动产生; 这里只补
    # "需要前端拿到结构化 payload"的关键事件。
    elif node_name == "evidence_plan":
        plan = node_output.get("evidence_plan", {}) or {}
        agents = plan.get("agents", []) or []
        yield make_event(
            "evidence_plan",
            "evidence_planned",
            message=f"取证计划: 派出 {len(agents)} 个专业 Agent",
            agents=agents,
            strategy=plan.get("strategy", ""),
        )

    elif node_name in {"log_agent", "metric_agent", "infra_agent", "runbook_agent"}:
        # 各专业 subagent 只回 Evidence (s06 课程范式); evidences 是 add-累加,
        # node_output 里只含本节点新增的那 (一或多) 条。
        new_evs = node_output.get("evidences", []) or []
        for ev in new_evs:
            yield make_event(
                "evidence",
                f"{node_name}_evidence",
                message=str(ev.get("summary") or "")[:200],
                agent=node_name,
                source=str(ev.get("source", "")),
                evidence_type=str(ev.get("type", "")),
            )

    elif node_name == "evidence_reducer":
        cands = node_output.get("candidates", []) or []
        yield make_event(
            "candidates",
            "candidates_reduced",
            message=f"归并得到 {len(cands)} 个候选根因",
            candidates=cands,
        )

    elif node_name == "rca_judge":
        rca = node_output.get("rca", {}) or {}
        if rca:
            yield make_event(
                "rca",
                "rca_judged",
                message=str(rca.get("root_cause") or "")[:200],
                rca=rca,
            )

    elif node_name == "remediation_planner":
        rem = node_output.get("remediation", {}) or {}
        if rem:
            yield make_event(
                "remediation",
                "remediation_planned",
                message=("处置建议待人工确认" if rem.get("requires_human_confirm") else "处置建议已生成"),
                remediation=rem,
            )

    elif node_name == "report":
        # deep graph 的最终 Report 节点; 复用 fast 的 type="report"
        # 让前端 SSE 同一套渲染逻辑能直接对接, 不必区分模式。
        response = node_output.get("response", "")
        if response:
            yield make_event(
                "report",
                "report_generated",
                message="深度诊断报告已生成",
                report=response,
                deep=True,
            )
