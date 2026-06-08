"""Alertmanager webhook 入账接口。

webhook 只做"入账+入队",不跑诊断: 校验 → 归一 → 去重 → 落 Postgres → 投 Redis 队列。
真正的诊断在独立进程 `python -m app.diagnosis_worker` 里跑。
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from loguru import logger
from pydantic import BaseModel, Field

from app.config import settings
from app.core import rate_limiter
from app.incidents.models import DiagnosisMode
from app.incidents.repository import incident_repository
from app.queue.redis_streams import incident_queue, level_for_severity

router = APIRouter(prefix="/webhook", tags=["webhook"])


class AlertmanagerAlert(BaseModel):
    """单条 Alertmanager 告警 (firing 或 resolved)。"""

    status: str = Field(default="firing", description="firing | resolved")
    labels: dict[str, Any] = Field(default_factory=dict)
    annotations: dict[str, Any] = Field(default_factory=dict)
    startsAt: str = Field(default="")
    endsAt: str = Field(default="")
    generatorURL: str = Field(default="")
    fingerprint: str = Field(default="")


class AlertmanagerPayload(BaseModel):
    """Alertmanager v4 webhook 完整 payload (一组告警)。"""

    version: str = Field(default="4")
    groupKey: str = Field(default="")
    truncatedAlerts: int = Field(default=0)
    status: str = Field(default="firing")
    receiver: str = Field(default="")
    groupLabels: dict[str, Any] = Field(default_factory=dict)
    commonLabels: dict[str, Any] = Field(default_factory=dict)
    commonAnnotations: dict[str, Any] = Field(default_factory=dict)
    externalURL: str = Field(default="")
    alerts: list[AlertmanagerAlert] = Field(default_factory=list)


def _format_alert_as_query(alert: AlertmanagerAlert) -> str:
    """把结构化告警渲染成紧凑的诊断 query 文本 (给 graph 当 input)。"""
    name = alert.labels.get("alertname", "UnknownAlert")
    severity = alert.labels.get("severity", "warning")
    instance = alert.labels.get("instance", "")
    service = alert.labels.get("service", "")
    summary = alert.annotations.get("summary", "")
    description = alert.annotations.get("description", "")
    runbook = alert.annotations.get("runbook_url", "")

    parts = [
        f"[{str(severity).upper()}] {name} alert firing",
        f"instance: {instance or '(unknown)'}",
    ]
    if service:
        parts.append(f"service: {service}")
    if summary:
        parts.append(f"summary: {summary}")
    if description:
        parts.append(f"description: {description}")
    if alert.startsAt:
        parts.append(f"startsAt: {alert.startsAt}")
    if runbook:
        parts.append(f"runbook: {runbook}")
    parts.append(
        "Act as an OnCall SRE. Diagnose likely root cause and provide remediation advice."
    )
    return "\n".join(parts)


def _diagnosis_mode_for(payload: AlertmanagerPayload, alert: AlertmanagerAlert) -> DiagnosisMode:
    """按确定性规则选 fast/deep 模式 (critical/page/p0/p1 或 ≥10 条告警 → deep)。"""
    severity = str(alert.labels.get("severity", "")).lower()
    if severity in {"critical", "page", "p0", "p1"}:
        return DiagnosisMode.DEEP
    if len(payload.alerts) >= 10:
        return DiagnosisMode.DEEP
    return DiagnosisMode.FAST


def _priority_for(alert: AlertmanagerAlert) -> int:
    severity = str(alert.labels.get("severity", "")).lower()
    if severity in {"critical", "page", "p0"}:
        return 10
    if severity in {"warning", "p1", "p2"}:
        return 50
    return 100


@router.post(
    "/alertmanager",
    summary="Alertmanager alert ingestion",
    description=(
        "Accept Alertmanager v4 payloads, persist alerts and incident groups, "
        "then enqueue diagnosis tasks to Redis Streams. The request returns quickly; "
        "diagnosis is performed by the worker process."
    ),
)
async def alertmanager_webhook(payload: AlertmanagerPayload, request: Request) -> dict[str, Any]:
    # 限流 (改造文档第 8 步): 单 IP/API Key 每秒 + 单来源(receiver)每分钟, 超限 429.
    # API Key 优先取 X-API-Key 头, 没有则用 IP; source 用 Alertmanager receiver。
    identity = request.headers.get("x-api-key") or rate_limiter.client_ip(request)
    await rate_limiter.enforce(
        "webhook_key", identity, settings.rate_limit_webhook_per_ip_per_sec, 1,
        detail="告警推送过于频繁 (单源每秒上限)",
    )
    source = str(payload.receiver or "default")
    await rate_limiter.enforce(
        "webhook_src", source, settings.rate_limit_webhook_per_source_per_min, 60,
        detail="该来源告警过于频繁 (单源每分钟上限)",
    )

    accepted: list[dict[str, Any]] = []
    skipped: list[str] = []
    failed: list[dict[str, Any]] = []

    for idx, alert in enumerate(payload.alerts):
        alertname = str(alert.labels.get("alertname", f"alert_{idx}"))
        instance = str(alert.labels.get("instance", "unknown"))
        if alert.status != "firing":
            skipped.append(alertname)
            continue

        query = _format_alert_as_query(alert)
        diagnosis_mode = _diagnosis_mode_for(payload, alert)
        priority = _priority_for(alert)

        try:
            result = await incident_repository.ingest_alertmanager_alert(
                payload=payload,
                alert=alert,
                query=query,
                diagnosis_mode=diagnosis_mode,
                priority=priority,
            )

            queue_message_id = ""
            enqueued = False
            if result.task_created:
                queue_message_id = await incident_queue.enqueue_task(
                    task_id=result.task_id,
                    incident_group_id=result.incident_group_id,
                    incident_id=result.incident_id,
                    diagnosis_mode=diagnosis_mode.value,
                    priority=priority,
                    level=level_for_severity(str(alert.labels.get("severity", ""))),
                    payload={
                        "query": query,
                        "alert_id": result.alert_id,
                        "alertname": alertname,
                        "severity": alert.labels.get("severity", ""),
                        "instance": instance,
                        "summary": alert.annotations.get("summary", ""),
                        "fingerprint": alert.fingerprint or "",
                        "startsAt": alert.startsAt,
                    },
                )
                await incident_repository.set_task_queue_message(
                    result.task_id, queue_message_id
                )
                enqueued = True

            accepted.append(
                {
                    "alertname": alertname,
                    "incident_group_id": result.incident_group_id,
                    "incident_id": result.incident_id,
                    "task_id": result.task_id,
                    "task_created": result.task_created,
                    "enqueued": enqueued,
                    "queue_message_id": queue_message_id,
                    "diagnosis_mode": diagnosis_mode.value,
                }
            )
        except Exception as exc:
            logger.exception(f"[webhook] alert={alertname} ingestion failed: {exc}")
            failed.append(
                {
                    "alertname": alertname,
                    "instance": instance,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    logger.info(
        f"[webhook] received={len(payload.alerts)} "
        f"accepted={len(accepted)} skipped={len(skipped)} failed={len(failed)}"
    )
    return {
        "status": "accepted",
        "received": len(payload.alerts),
        "accepted": accepted,
        "skipped": skipped,
        "failed": failed,
    }


@router.get(
    "/history",
    summary="Recent diagnosis tasks",
    description="Compatibility endpoint: returns recent queued/processed diagnosis tasks.",
)
async def get_history(limit: int = 20) -> dict[str, Any]:
    items = await incident_repository.list_recent_tasks(limit=limit)
    return {"count": len(items), "items": items}


@router.delete(
    "/history",
    summary="Legacy no-op",
    description="The new pipeline stores task history in Postgres; destructive clearing is disabled.",
)
async def clear_history() -> dict[str, Any]:
    return {
        "status": "disabled",
        "message": "Incident history is stored in Postgres and is not cleared by this endpoint.",
    }
