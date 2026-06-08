"""Worker 审计包装: 把一次 Agent 执行变成可审计的记录链。

跑一次诊断 = 创建一条 AgentRun + 收集 N 条 Evidence(alert_payload/tool_call/
diagnosis_step/diagnosis_report) + 记 ToolCall 行 + 最终 finish_run 落定状态/usage。
本模块不知道 Redis 队列、SSE、HTTP, 只对 orchestration.diagnosis_runner 的事件流
做"写审计"的副作用。供 Worker 调; 手动 SSE 路径不进这里(无 task_id 事实行)。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from app.orchestration.repository import agent_run_repository
from app.evidence.models import EvidenceCreate
from app.evidence.repository import evidence_repository
from app.incidents.models import EvidenceSource
from app.incidents.repository import incident_repository


@dataclass
class DiagnosisRunResult:
    report: str = ""
    agent_run_id: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    tool_call_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


def _extract_payload(item: dict[str, Any], task: dict[str, Any] | None) -> dict[str, Any]:
    payload = item.get("payload") or {}
    if payload:
        return payload
    if task:
        return task.get("payload") or {}
    return {}


def _event_data(event: dict[str, Any]) -> dict[str, Any]:
    data = event.get("data")
    return data if isinstance(data, dict) else {}


async def run_legacy_langgraph_with_audit(task_id: str, item: dict[str, Any]) -> DiagnosisRunResult:
    """跑 LangGraph 诊断图, 并把整条证据链落库。

    Worker 入口: 每个任务都会写出 AgentRun + 多条 Evidence(含 alert_payload / tool_call /
    diagnosis_step / diagnosis_report)+ ToolCall 行 + 最终任务结果。
    """
    from app.orchestration.diagnosis_runner import run_diagnosis_graph

    task = await incident_repository.get_task(task_id)
    payload = _extract_payload(item, task)
    query = payload.get("query") or ""
    if not query:
        raise ValueError("diagnosis task payload missing query")
    diagnosis_mode = str(
        item.get("diagnosis_mode")
        or (task or {}).get("diagnosis_mode")
        or payload.get("diagnosis_mode")
        or "fast"
    )

    incident_group_id = str(item.get("incident_group_id") or (task or {}).get("incident_group_id") or "")
    incident_id = str(item.get("incident_id") or (task or {}).get("incident_id") or "")
    if not incident_group_id or not incident_id:
        raise ValueError("diagnosis task missing incident ids")

    # 算告警指纹透传进 graph state, 供 LLM Wiki recall_block 做直达页查找
    # (services/<service>.md, patterns/<sig>.md)。指纹取持久化 task.payload
    # (含 _extract_service 提取的 service) 而非 _extract_payload 取到的队列消息
    # payload (后者缺 service 字段)。
    from app.incidents.signature import alert_view, compute_alert_signature

    task_payload = (task or {}).get("payload")
    if not isinstance(task_payload, dict):
        task_payload = payload  # 退化: 极少数无 task 行的调用, 用已取到的 payload
    alert_signature = compute_alert_signature(alert_view(task_payload))

    result = DiagnosisRunResult()

    # 重试复用已有 AgentRun + alert Evidence。
    # 为什么需要: 本 wrapper 起手写的 alert Evidence + AgentRun 是无条件的;
    # 不复用就会每次重试各写一份, 制造重复审计行。复用同时把历史 evidence_ids 续上,
    # 让最终成功的 run 仍能列出跨多次尝试产生的全部 Evidence。
    existing_runs = await agent_run_repository.list_runs_for_task(task_id)
    resume_run = existing_runs[0] if existing_runs else None

    if resume_run and resume_run.get("input_ref"):
        run_id = str(resume_run["id"])
        input_evidence_id = str(resume_run["input_ref"])
        result.agent_run_id = run_id
        prior_evidence = resume_run.get("evidence_ids")
        if isinstance(prior_evidence, list) and prior_evidence:
            result.evidence_ids.extend(str(e) for e in prior_evidence)
        else:
            result.evidence_ids.append(input_evidence_id)
    else:
        input_evidence_id = await evidence_repository.create(
            EvidenceCreate(
                incident_group_id=incident_group_id,
                incident_id=incident_id,
                source=EvidenceSource.ALERT,
                type="alert_payload",
                summary=str(payload.get("summary") or payload.get("alertname") or "Alert payload"),
                content=payload,
                metadata={"task_id": task_id},
            )
        )
        result.evidence_ids.append(input_evidence_id)
        run_id = await agent_run_repository.create_run(
            task_id=task_id,
            incident_group_id=incident_group_id,
            incident_id=incident_id,
            agent_name="legacy_langgraph_agent",
            agent_version="v3",
            input_ref=input_evidence_id,
        )
        result.agent_run_id = run_id

    report_evidence_id = ""

    try:
        session_id = f"task-{task_id}"
        async for event in run_diagnosis_graph(
            query,
            session_id=session_id,
            diagnosis_mode=diagnosis_mode,
            cache_reports=False,
            alert_signature=alert_signature,
        ):
            event_type = str(event.get("type") or "")
            data = _event_data(event)

            if event_type == "error":
                raise RuntimeError(
                    str(event.get("message") or data.get("error_type") or "diagnosis failed")
                )
            if event_type == "tool_call":
                await _persist_tool_call_event(
                    task_id=task_id,
                    incident_group_id=incident_group_id,
                    incident_id=incident_id,
                    run_id=run_id,
                    event=event,
                    result=result,
                )
            elif event_type == "step_complete":
                evidence_id = await evidence_repository.create(
                    EvidenceCreate(
                        incident_group_id=incident_group_id,
                        incident_id=incident_id,
                        source=EvidenceSource.MCP_TOOL_RESULT,
                        type="diagnosis_step",
                        summary=str(data.get("step") or event.get("message") or "diagnosis step"),
                        content={"event": event},
                        metadata={"task_id": task_id, "agent_run_id": run_id},
                    )
                )
                result.evidence_ids.append(evidence_id)
            elif event_type == "report":
                result.report = str(data.get("report") or result.report)
                report_evidence_id = await evidence_repository.create(
                    EvidenceCreate(
                        incident_group_id=incident_group_id,
                        incident_id=incident_id,
                        source=EvidenceSource.RCA,
                        type="diagnosis_report",
                        summary="Final diagnosis report",
                        content={"report": result.report, "event": event},
                        metadata={"task_id": task_id, "agent_run_id": run_id},
                    )
                )
                result.evidence_ids.append(report_evidence_id)
            elif event_type == "usage":
                result.input_tokens += int(data.get("input_tokens") or event.get("input_tokens") or 0)
                result.output_tokens += int(data.get("output_tokens") or event.get("output_tokens") or 0)
                result.total_tokens += int(data.get("total_tokens") or event.get("total_tokens") or 0)
            elif event_type == "stats":
                result.input_tokens += int(data.get("input_tokens") or 0)
                result.output_tokens += int(data.get("output_tokens") or 0)
                result.total_tokens += int(data.get("total_tokens") or 0)

        await agent_run_repository.finish_run(
            run_id,
            status="succeeded",
            output_ref=report_evidence_id,
            evidence_ids=result.evidence_ids,
            tool_call_count=result.tool_call_count,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            total_tokens=result.total_tokens,
        )
        return result
    except asyncio.CancelledError:
        # 这里通常来自 Worker 的任务 timeout 或进程关闭。
        # 为什么要显式收尾:
        # - 如果不更新 AgentRun, Postgres 里会留下 running 状态;
        # - 任务本身由 Worker 决定 retry / DLQ, 这里仅把本次 AgentRun 标成 cancelled。
        await agent_run_repository.finish_run(
            run_id,
            status="cancelled",
            evidence_ids=result.evidence_ids,
            tool_call_count=result.tool_call_count,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            total_tokens=result.total_tokens,
            error="cancelled by worker timeout or shutdown",
        )
        raise
    except Exception as exc:
        await agent_run_repository.finish_run(
            run_id,
            status="failed",
            evidence_ids=result.evidence_ids,
            tool_call_count=result.tool_call_count,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            total_tokens=result.total_tokens,
            error=f"{type(exc).__name__}: {exc}",
        )
        raise


async def _persist_tool_call_event(
    *,
    task_id: str,
    incident_group_id: str,
    incident_id: str,
    run_id: str,
    event: dict[str, Any],
    result: DiagnosisRunResult,
) -> None:
    data = _event_data(event)
    tool_name = str(data.get("name") or event.get("name") or "unknown_tool")
    status = str(data.get("status") or event.get("status") or "ok")
    elapsed_ms = int(data.get("elapsed_ms") or event.get("elapsed_ms") or 0)
    content = {"event": event}

    evidence_id = await evidence_repository.create(
        EvidenceCreate(
            incident_group_id=incident_group_id,
            incident_id=incident_id,
            source=EvidenceSource.MCP_TOOL_RESULT,
            type="tool_call",
            summary=f"{tool_name} -> {status}",
            content=content,
            metadata={"task_id": task_id, "agent_run_id": run_id},
        )
    )
    result.evidence_ids.append(evidence_id)
    result.tool_call_count += 1
    await agent_run_repository.record_tool_call(
        agent_run_id=run_id,
        task_id=task_id,
        incident_group_id=incident_group_id,
        tool_name=tool_name,
        status=status,
        args={
            "read_only": bool(data.get("read_only") or event.get("read_only") or False),
            "result_chars": int(data.get("result_chars") or event.get("result_chars") or 0),
        },
        result_ref=evidence_id,
        elapsed_ms=elapsed_ms,
        error="" if status == "ok" else status,
    )
