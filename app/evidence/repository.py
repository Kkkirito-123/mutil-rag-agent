"""Repository for the Evidence Store."""

from __future__ import annotations

import json
from typing import Any

from app.core.db_utils import json_dump, new_id
from app.db.postgres import get_pool
from app.evidence.models import EvidenceCreate


def _loads(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except Exception:
        return value


def _row_to_dict(row: Any | None) -> dict[str, Any] | None:
    if row is None:
        return None
    item = dict(row)
    for key in ("content", "metadata"):
        if key in item:
            item[key] = _loads(item[key])
    return item


class EvidenceRepository:
    async def create(self, evidence: EvidenceCreate) -> str:
        evidence_id = new_id("ev")
        source = getattr(evidence.source, "value", evidence.source)
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO evidence (
                    id, incident_group_id, incident_id, source, type, summary,
                    content, score, occurred_at, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9, $10::jsonb)
                """,
                evidence_id,
                evidence.incident_group_id,
                evidence.incident_id,
                str(source),
                evidence.type,
                evidence.summary,
                json_dump(evidence.content),
                evidence.score,
                evidence.occurred_at,
                json_dump(evidence.metadata),
            )
        return evidence_id

    async def list_for_incident_group(
        self,
        incident_group_id: str,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 500))
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM evidence
                WHERE incident_group_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                incident_group_id,
                limit,
            )
        return [_row_to_dict(row) or {} for row in rows]

    async def list_for_task(self, task_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 500))
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT ev.*
                FROM evidence ev
                JOIN diagnosis_tasks dt ON dt.incident_group_id = ev.incident_group_id
                WHERE dt.id = $1
                ORDER BY ev.created_at DESC
                LIMIT $2
                """,
                task_id,
                limit,
            )
        return [_row_to_dict(row) or {} for row in rows]


evidence_repository = EvidenceRepository()

