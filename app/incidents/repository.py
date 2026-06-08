"""Postgres repository for alerts, incident groups, and diagnosis tasks."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from loguru import logger

from app.config import settings
from app.core.db_utils import json_dump, new_id
from app.db.postgres import get_pool
from app.incidents.models import (
    AlertStatus,
    DiagnosisMode,
    DiagnosisTaskStatus,
    IncidentIngestResult,
    NormalizedAlert,
)


def _stable_id(prefix: str, value: str, length: int = 24) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]
    return f"{prefix}_{digest}"


def _loads_if_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    if not value or value[0] not in "[{":
        return value
    try:
        return json.loads(value)
    except Exception:
        return value


def _record_to_dict(record: Any | None) -> dict[str, Any] | None:
    if record is None:
        return None
    row = dict(record)
    for key in ("labels", "annotations", "raw_payload", "metadata", "payload", "content", "evidence_ids"):
        if key in row:
            row[key] = _loads_if_json(row[key])
    return row


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _time_bucket(dt: datetime | None) -> int:
    base = dt or datetime.now(timezone.utc)
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    bucket = max(1, settings.incident_time_bucket_sec)
    return int(base.timestamp()) // bucket * bucket


def _extract_service(labels: dict[str, Any]) -> str:
    for key in ("service", "service_name", "app", "job", "container", "pod"):
        value = labels.get(key)
        if value:
            return str(value)
    return ""


def _normalize_alert(payload: Any, alert: Any, query: str) -> NormalizedAlert:
    labels = dict(getattr(alert, "labels", {}) or {})
    annotations = dict(getattr(alert, "annotations", {}) or {})
    alertname = str(labels.get("alertname") or "UnknownAlert")
    instance = str(labels.get("instance") or "")
    receiver = str(getattr(payload, "receiver", "") or "")
    group_key = str(getattr(payload, "groupKey", "") or "")
    starts_at = _parse_datetime(getattr(alert, "startsAt", "") or None)
    ends_at = _parse_datetime(getattr(alert, "endsAt", "") or None)
    fingerprint = str(getattr(alert, "fingerprint", "") or "")
    if not fingerprint:
        fingerprint = _stable_id(
            "fp",
            f"{alertname}:{instance}:{starts_at.isoformat() if starts_at else ''}",
            length=16,
        )

    bucket = _time_bucket(starts_at)
    idempotency_key = f"{receiver}:{group_key}:{fingerprint}:{bucket}:{getattr(alert, 'status', 'firing')}"
    alert_id = _stable_id("al", idempotency_key)

    raw_payload = {
        "externalURL": getattr(payload, "externalURL", ""),
        "groupLabels": getattr(payload, "groupLabels", {}) or {},
        "commonLabels": getattr(payload, "commonLabels", {}) or {},
        "commonAnnotations": getattr(payload, "commonAnnotations", {}) or {},
        "generatorURL": getattr(alert, "generatorURL", ""),
        "truncatedAlerts": getattr(payload, "truncatedAlerts", 0),
    }

    return NormalizedAlert(
        id=alert_id,
        idempotency_key=idempotency_key,
        fingerprint=fingerprint,
        status=AlertStatus(getattr(alert, "status", "firing") or "firing"),
        alertname=alertname,
        severity=str(labels.get("severity") or "warning"),
        service=_extract_service(labels),
        instance=instance,
        receiver=receiver,
        group_key=group_key,
        labels=labels,
        annotations=annotations,
        raw_payload=raw_payload,
        query=query,
        starts_at=starts_at,
        ends_at=ends_at,
    )


def _correlation_key(payload: Any, alert: NormalizedAlert) -> str:
    if alert.group_key:
        return f"alertmanager:{alert.receiver}:{alert.group_key}"
    labels = alert.labels
    cluster = labels.get("cluster") or labels.get("cluster_name") or ""
    namespace = labels.get("namespace") or labels.get("kubernetes_namespace") or ""
    service = alert.service or alert.instance or "unknown"
    bucket = _time_bucket(alert.starts_at)
    return f"window:{cluster}:{namespace}:{service}:{bucket}"


def _summary(payload: Any, alert: NormalizedAlert) -> str:
    common = getattr(payload, "commonAnnotations", {}) or {}
    return (
        str(common.get("summary") or "")
        or str(alert.annotations.get("summary") or "")
        or str(alert.annotations.get("description") or "")
        or f"{alert.alertname} on {alert.service or alert.instance or 'unknown'}"
    )


class IncidentRepository:
    """Repository for the first industrial Incident pipeline."""

    async def ingest_alertmanager_alert(
        self,
        *,
        payload: Any,
        alert: Any,
        query: str,
        diagnosis_mode: DiagnosisMode = DiagnosisMode.FAST,
        priority: int = 100,
    ) -> IncidentIngestResult:
        """Persist alert, correlate it, and create a diagnosis task when needed."""
        normalized = _normalize_alert(payload, alert, query)
        correlation_key = _correlation_key(payload, normalized)
        incident_group_id = _stable_id("ig", correlation_key)
        incident_id = _stable_id("inc", incident_group_id)
        labels = dict(getattr(payload, "commonLabels", {}) or {})
        labels.update(normalized.labels)
        metadata = {
            "receiver": normalized.receiver,
            "group_key": normalized.group_key,
            "external_url": getattr(payload, "externalURL", ""),
            "source": "alertmanager",
        }

        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                await self._upsert_alert(conn, normalized)
                await self._upsert_incident_group(
                    conn,
                    incident_group_id=incident_group_id,
                    correlation_key=correlation_key,
                    alert=normalized,
                    summary=_summary(payload, normalized),
                    labels=labels,
                    metadata=metadata,
                )
                await self._upsert_incident(
                    conn,
                    incident_id=incident_id,
                    incident_group_id=incident_group_id,
                    alert=normalized,
                    title=_summary(payload, normalized),
                    metadata=metadata,
                )
                await conn.execute(
                    """
                    INSERT INTO incident_group_alerts (incident_group_id, alert_id)
                    VALUES ($1, $2)
                    ON CONFLICT DO NOTHING
                    """,
                    incident_group_id,
                    normalized.id,
                )
                await conn.execute(
                    """
                    UPDATE incident_groups
                    SET alert_count = (
                        SELECT count(*) FROM incident_group_alerts
                        WHERE incident_group_id = $1
                    ),
                    updated_at = now()
                    WHERE id = $1
                    """,
                    incident_group_id,
                )
                task_id, task_created = await self._create_or_get_task(
                    conn,
                    incident_group_id=incident_group_id,
                    incident_id=incident_id,
                    query=query,
                    alert=normalized,
                    diagnosis_mode=diagnosis_mode,
                    priority=priority,
                )

        return IncidentIngestResult(
            alert_id=normalized.id,
            incident_group_id=incident_group_id,
            incident_id=incident_id,
            correlation_key=correlation_key,
            task_id=task_id,
            task_created=task_created,
        )

    async def _upsert_alert(self, conn: Any, alert: NormalizedAlert) -> None:
        await conn.execute(
            """
            INSERT INTO alerts (
                id, idempotency_key, fingerprint, status, alertname, severity,
                service, instance, receiver, group_key, labels, annotations,
                raw_payload, query, starts_at, ends_at
            )
            VALUES (
                $1, $2, $3, $4, $5, $6,
                $7, $8, $9, $10, $11::jsonb, $12::jsonb,
                $13::jsonb, $14, $15, $16
            )
            ON CONFLICT (idempotency_key) DO UPDATE SET
                status = EXCLUDED.status,
                labels = EXCLUDED.labels,
                annotations = EXCLUDED.annotations,
                raw_payload = EXCLUDED.raw_payload,
                query = EXCLUDED.query,
                ends_at = EXCLUDED.ends_at,
                last_seen = now(),
                seen_count = alerts.seen_count + 1
            """,
            alert.id,
            alert.idempotency_key,
            alert.fingerprint,
            alert.status.value,
            alert.alertname,
            alert.severity,
            alert.service,
            alert.instance,
            alert.receiver,
            alert.group_key,
            json_dump(alert.labels),
            json_dump(alert.annotations),
            json_dump(alert.raw_payload),
            alert.query,
            alert.starts_at,
            alert.ends_at,
        )

    async def _upsert_incident_group(
        self,
        conn: Any,
        *,
        incident_group_id: str,
        correlation_key: str,
        alert: NormalizedAlert,
        summary: str,
        labels: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        await conn.execute(
            """
            INSERT INTO incident_groups (
                id, correlation_key, status, severity, primary_service,
                summary, labels, metadata
            )
            VALUES ($1, $2, 'open', $3, $4, $5, $6::jsonb, $7::jsonb)
            ON CONFLICT (correlation_key) DO UPDATE SET
                severity = EXCLUDED.severity,
                primary_service = COALESCE(NULLIF(incident_groups.primary_service, ''), EXCLUDED.primary_service),
                summary = COALESCE(NULLIF(incident_groups.summary, ''), EXCLUDED.summary),
                labels = incident_groups.labels || EXCLUDED.labels,
                metadata = incident_groups.metadata || EXCLUDED.metadata,
                updated_at = now()
            """,
            incident_group_id,
            correlation_key,
            alert.severity,
            alert.service,
            summary,
            json_dump(labels),
            json_dump(metadata),
        )

    async def _upsert_incident(
        self,
        conn: Any,
        *,
        incident_id: str,
        incident_group_id: str,
        alert: NormalizedAlert,
        title: str,
        metadata: dict[str, Any],
    ) -> None:
        await conn.execute(
            """
            INSERT INTO incidents (
                id, incident_group_id, status, title, severity, service,
                started_at, metadata
            )
            VALUES ($1, $2, 'open', $3, $4, $5, $6, $7::jsonb)
            ON CONFLICT (id) DO UPDATE SET
                title = COALESCE(NULLIF(incidents.title, ''), EXCLUDED.title),
                severity = EXCLUDED.severity,
                service = COALESCE(NULLIF(incidents.service, ''), EXCLUDED.service),
                metadata = incidents.metadata || EXCLUDED.metadata,
                updated_at = now()
            """,
            incident_id,
            incident_group_id,
            title,
            alert.severity,
            alert.service,
            alert.starts_at,
            json_dump(metadata),
        )

    async def _create_or_get_task(
        self,
        conn: Any,
        *,
        incident_group_id: str,
        incident_id: str,
        query: str,
        alert: NormalizedAlert,
        diagnosis_mode: DiagnosisMode,
        priority: int,
    ) -> tuple[str, bool]:
        # 去重幂等 (改造文档第 7 步): 不再 SELECT-then-INSERT (并发下两条相同告警可能
        # 同时查不到再各插一条). 改成依赖部分唯一索引 idx_diagnosis_task_dedup_active
        # (dedup_key WHERE status IN pending/running) 做 INSERT ON CONFLICT, 由数据库
        # 原子保证 "同一 dedup_key 活跃任务唯一". dedup_key 用 incident_group_id, 即
        # "一个告警组同时只有一个在跑的诊断", 与原行为一致但无竞态.
        task_id = new_id("task")
        dedup_key = incident_group_id
        payload = {
            "query": query,
            "alert_id": alert.id,
            "alertname": alert.alertname,
            "severity": alert.severity,
            "service": alert.service,
            "instance": alert.instance,
            "fingerprint": alert.fingerprint,
        }
        row = await conn.fetchrow(
            """
            INSERT INTO diagnosis_tasks (
                id, incident_group_id, incident_id, status, priority,
                diagnosis_mode, max_attempts, payload, dedup_key, last_seen_at
            )
            VALUES ($1, $2, $3, 'pending', $4, $5, $6, $7::jsonb, $8, now())
            ON CONFLICT (dedup_key) WHERE status IN ('pending', 'running')
            DO UPDATE SET
                repeat_count = diagnosis_tasks.repeat_count + 1,
                last_seen_at = now(),
                updated_at = now()
            RETURNING id, (xmax = 0) AS inserted
            """,
            task_id,
            incident_group_id,
            incident_id,
            priority,
            diagnosis_mode.value,
            settings.diagnosis_task_max_attempts,
            json_dump(payload),
            dedup_key,
        )
        # xmax = 0 表示这是真正的新插入; 否则是命中已有活跃任务被 DO UPDATE.
        returned_id = str(row["id"])
        task_created = bool(row["inserted"])
        return returned_id, task_created

    async def set_task_queue_message(self, task_id: str, message_id: str) -> None:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE diagnosis_tasks
                SET queue_message_id = $2, updated_at = now()
                WHERE id = $1
                """,
                task_id,
                message_id,
            )

    async def mark_task_running(self, task_id: str) -> None:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE diagnosis_tasks
                SET status = 'running',
                    attempts = attempts + 1,
                    claimed_at = now(),
                    updated_at = now(),
                    error = ''
                WHERE id = $1
                """,
                task_id,
            )

    async def mark_task_succeeded(
        self,
        task_id: str,
        *,
        report: str = "",
        agent_run_id: str = "",
        evidence_ids: list[str] | None = None,
    ) -> None:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE diagnosis_tasks
                SET status = 'succeeded',
                    finished_at = now(),
                    updated_at = now(),
                    payload = payload || $2::jsonb
                WHERE id = $1
                """,
                task_id,
                json_dump(
                    {
                        "report": report,
                        "agent_run_id": agent_run_id,
                        "evidence_ids": evidence_ids or [],
                    }
                ),
            )

    async def mark_task_failed(self, task_id: str, error: str) -> None:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE diagnosis_tasks
                SET status = 'failed',
                    error = $2,
                    finished_at = now(),
                    updated_at = now()
                WHERE id = $1
                """,
                task_id,
                error[:4000],
            )

    async def mark_task_retry_pending(self, task_id: str, error: str) -> None:
        """Mark a failed attempt as retryable instead of final failed.

        为什么加在 repository:
        - diagnosis_tasks 的事实状态属于 Postgres, 不属于 Redis;
        - Worker 只决定"这次失败是否还能重试";
        - 具体怎么更新任务状态集中在 repository, 避免 SQL 散落在 Worker 里。

        预期效果:
        - 任务单次失败后回到 pending, 可以重新入队;
        - attempts 保留历史尝试次数, 便于到达 max_attempts 后进入 DLQ。
        """
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE diagnosis_tasks
                SET status = 'pending',
                    error = $2,
                    claimed_at = NULL,
                    updated_at = now()
                WHERE id = $1
                """,
                task_id,
                error[:4000],
            )

    async def get_task(self, task_id: str) -> dict[str, Any] | None:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM diagnosis_tasks WHERE id = $1", task_id)
        return _record_to_dict(row)

    async def get_incident_group(self, incident_group_id: str) -> dict[str, Any] | None:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM incident_groups WHERE id = $1",
                incident_group_id,
            )
        return _record_to_dict(row)

    async def create_manual_task(
        self,
        *,
        source: str,
        title: str,
        query: str,
        severity: str = "warning",
        service: str = "",
        diagnosis_mode: DiagnosisMode = DiagnosisMode.FAST,
        priority: int = 100,
        context: dict[str, Any] | None = None,
    ) -> IncidentIngestResult:
        """无 Alertmanager 上下文的手动建任务 (聊天升级 / 命令行触发 / 外部对接).

        和 ingest_alertmanager_alert 共享同一张事实表, 让"手动诊断"也能在事件中心、
        证据链、Wiki ingest 里被统一看到, 而不是漂在另一条隐形通道上.

        为什么不复用 ingest_alertmanager_alert: AM payload 太重 (receiver/groupKey/labels),
        手动场景没有这些字段; 构造一个假 payload 会引入 fingerprint 不稳定的副作用.
        """
        now = datetime.now(timezone.utc)
        correlation_key = f"manual:{source}:{_stable_id('mc', f'{source}|{title}|{query[:200]}', length=16)}"
        incident_group_id = _stable_id("ig", correlation_key)
        incident_id = _stable_id("inc", incident_group_id)

        # 合成一条 NormalizedAlert 占位 (用于复用 _upsert_alert 的 schema)
        synthetic_alertname = (title or query[:80] or "ManualEscalation").strip()
        idempotency_key = f"manual:{source}:{_stable_id('ak', f'{title}|{query[:200]}', length=24)}"
        fingerprint = _stable_id("fp", correlation_key, length=16)
        synth_alert = NormalizedAlert(
            id=_stable_id("al", idempotency_key),
            idempotency_key=idempotency_key,
            fingerprint=fingerprint,
            status=AlertStatus.FIRING,
            alertname=synthetic_alertname,
            severity=severity or "warning",
            service=service or "",
            instance="",
            receiver=source,
            group_key="",
            labels={"source": source, "manual": "true"},
            annotations={"summary": title or query[:200]},
            raw_payload={"source": source, "context": context or {}},
            query=query or title or "",
            starts_at=now,
            ends_at=None,
        )

        summary_text = (title or query or synthetic_alertname).strip()[:500]
        metadata = {
            "source": source,
            "manual": True,
            "context": context or {},
        }

        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                await self._upsert_alert(conn, synth_alert)
                await self._upsert_incident_group(
                    conn,
                    incident_group_id=incident_group_id,
                    correlation_key=correlation_key,
                    alert=synth_alert,
                    summary=summary_text,
                    labels=dict(synth_alert.labels),
                    metadata=metadata,
                )
                await self._upsert_incident(
                    conn,
                    incident_id=incident_id,
                    incident_group_id=incident_group_id,
                    alert=synth_alert,
                    title=summary_text,
                    metadata=metadata,
                )
                await conn.execute(
                    """
                    INSERT INTO incident_group_alerts (incident_group_id, alert_id)
                    VALUES ($1, $2)
                    ON CONFLICT DO NOTHING
                    """,
                    incident_group_id,
                    synth_alert.id,
                )
                task_id, task_created = await self._create_or_get_task(
                    conn,
                    incident_group_id=incident_group_id,
                    incident_id=incident_id,
                    query=query or title,
                    alert=synth_alert,
                    diagnosis_mode=diagnosis_mode,
                    priority=priority,
                )

        return IncidentIngestResult(
            alert_id=synth_alert.id,
            incident_group_id=incident_group_id,
            incident_id=incident_id,
            correlation_key=correlation_key,
            task_id=task_id,
            task_created=task_created,
        )

    async def queue_position(self, task_id: str) -> int | None:
        """估算某个 pending 任务的排队位置 (前面还有几个在排, 含自己 = 1-based)。

        口径: 按 created_at 先到先服务, 数所有 created_at <= 本任务且仍 pending 的任务数。
        running 的不计入 (已在被处理)。任务不存在 / 非 pending 返回 None。
        """
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT count(*) AS pos
                FROM diagnosis_tasks
                WHERE status = 'pending'
                  AND created_at <= (
                      SELECT created_at FROM diagnosis_tasks WHERE id = $1 AND status = 'pending'
                  )
                """,
                task_id,
            )
        if row is None or row["pos"] is None or int(row["pos"]) == 0:
            return None
        return int(row["pos"])

    async def list_recent_tasks(self, limit: int = 20) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 100))
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM diagnosis_tasks
                ORDER BY created_at DESC
                LIMIT $1
                """,
                limit,
            )
        return [_record_to_dict(row) or {} for row in rows]

    async def delete_task(self, task_id: str) -> dict[str, Any] | None:
        """Delete a terminal diagnosis task and its owned audit records.

        Evidence is scoped to an incident/group rather than directly to a task.
        When this is the last task for the group, deleting the group cascades the
        whole event. Otherwise, only an incident no longer referenced by another
        task is removed with its evidence.
        """
        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                return await self._delete_task_with_conn(conn, task_id)

    async def delete_tasks(self, task_ids: list[str]) -> dict[str, Any]:
        """Delete several terminal tasks in one transaction and one API call."""
        unique_ids = sorted({task_id.strip() for task_id in task_ids if task_id.strip()})
        results: list[dict[str, Any]] = []
        skipped_active: list[str] = []
        not_found: list[str] = []

        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                for task_id in unique_ids:
                    try:
                        result = await self._delete_task_with_conn(conn, task_id)
                    except ValueError:
                        skipped_active.append(task_id)
                        continue
                    if result is None:
                        not_found.append(task_id)
                    else:
                        results.append(result)

        return {
            "requested": len(unique_ids),
            "deleted": len(results),
            "skipped_active": skipped_active,
            "not_found": not_found,
            "items": results,
        }

    async def _delete_task_with_conn(
        self,
        conn: Any,
        task_id: str,
    ) -> dict[str, Any] | None:
        task = await conn.fetchrow(
            """
            SELECT id, status, incident_group_id, incident_id
            FROM diagnosis_tasks
            WHERE id = $1
            FOR UPDATE
            """,
            task_id,
        )
        if task is None:
            return None

        status = str(task["status"] or "")
        if status in {"pending", "running"}:
            raise ValueError("排队中或进行中的任务不能删除")

        group_id = str(task["incident_group_id"])
        incident_id = str(task["incident_id"])
        other_group_tasks = int(
            await conn.fetchval(
                """
                SELECT count(*)
                FROM diagnosis_tasks
                WHERE incident_group_id = $1 AND id <> $2
                """,
                group_id,
                task_id,
            )
            or 0
        )

        deleted_tool_calls = int(
            await conn.fetchval(
                "SELECT count(*) FROM tool_calls WHERE task_id = $1",
                task_id,
            )
            or 0
        )
        deleted_agent_runs = int(
            await conn.fetchval(
                "SELECT count(*) FROM agent_runs WHERE task_id = $1",
                task_id,
            )
            or 0
        )
        deleted_approvals = int(
            await conn.fetchval(
                "SELECT count(*) FROM approval_requests WHERE task_id = $1",
                task_id,
            )
            or 0
        )

        if other_group_tasks == 0:
            alert_ids = await conn.fetch(
                """
                SELECT alert_id
                FROM incident_group_alerts
                WHERE incident_group_id = $1
                """,
                group_id,
            )
            deleted_evidence = int(
                await conn.fetchval(
                    "SELECT count(*) FROM evidence WHERE incident_group_id = $1",
                    group_id,
                )
                or 0
            )
            await conn.execute(
                "DELETE FROM approval_requests WHERE incident_group_id = $1",
                group_id,
            )
            await conn.execute("DELETE FROM incident_groups WHERE id = $1", group_id)
            orphan_alert_ids = [str(row["alert_id"]) for row in alert_ids]
            if orphan_alert_ids:
                await conn.execute(
                    """
                    DELETE FROM alerts a
                    WHERE a.id = ANY($1::text[])
                      AND NOT EXISTS (
                          SELECT 1
                          FROM incident_group_alerts iga
                          WHERE iga.alert_id = a.id
                      )
                    """,
                    orphan_alert_ids,
                )
            return {
                "task_id": task_id,
                "incident_group_id": group_id,
                "group_deleted": True,
                "deleted_evidence": deleted_evidence,
                "deleted_agent_runs": deleted_agent_runs,
                "deleted_tool_calls": deleted_tool_calls,
                "deleted_approvals": deleted_approvals,
            }

        await conn.execute("DELETE FROM approval_requests WHERE task_id = $1", task_id)
        await conn.execute("DELETE FROM tool_calls WHERE task_id = $1", task_id)
        await conn.execute("DELETE FROM agent_runs WHERE task_id = $1", task_id)
        await conn.execute("DELETE FROM diagnosis_tasks WHERE id = $1", task_id)

        other_incident_tasks = int(
            await conn.fetchval(
                "SELECT count(*) FROM diagnosis_tasks WHERE incident_id = $1",
                incident_id,
            )
            or 0
        )
        deleted_evidence = 0
        if other_incident_tasks == 0:
            deleted_evidence = int(
                await conn.fetchval(
                    "SELECT count(*) FROM evidence WHERE incident_id = $1",
                    incident_id,
                )
                or 0
            )
            await conn.execute("DELETE FROM evidence WHERE incident_id = $1", incident_id)
            await conn.execute("DELETE FROM incidents WHERE id = $1", incident_id)

        return {
            "task_id": task_id,
            "incident_group_id": group_id,
            "group_deleted": False,
            "deleted_evidence": deleted_evidence,
            "deleted_agent_runs": deleted_agent_runs,
            "deleted_tool_calls": deleted_tool_calls,
            "deleted_approvals": deleted_approvals,
        }


incident_repository = IncidentRepository()
