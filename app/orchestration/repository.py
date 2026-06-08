"""AgentRun 与 ToolCall 仓储。

裸 SQL + asyncpg, 不上 ORM (参考 app/incidents/repository.py 风格)。
为 orchestration/audit.py 在 Worker 路径里的审计落库提供原子操作。
"""

from __future__ import annotations

import json
from typing import Any

from app.core.db_utils import json_dump, new_id
from app.db.postgres import get_pool


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
    for key in ("args", "evidence_ids"):
        if key in item:
            item[key] = _loads(item[key])
    return item


class AgentRunRepository:
    async def create_run(
        self,
        *,
        task_id: str,
        incident_group_id: str,
        incident_id: str,
        agent_name: str,
        agent_version: str = "v1",
        input_ref: str = "",
    ) -> str:
        run_id = new_id("run")
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO agent_runs (
                    id, task_id, incident_group_id, incident_id, agent_name,
                    agent_version, status, input_ref, started_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, 'running', $7, now())
                """,
                run_id,
                task_id,
                incident_group_id,
                incident_id,
                agent_name,
                agent_version,
                input_ref,
            )
        return run_id

    async def finish_run(
        self,
        run_id: str,
        *,
        status: str,
        output_ref: str = "",
        evidence_ids: list[str] | None = None,
        tool_call_count: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
        error: str = "",
    ) -> None:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE agent_runs
                SET status = $2,
                    output_ref = $3,
                    evidence_ids = $4::jsonb,
                    tool_call_count = $5,
                    input_tokens = $6,
                    output_tokens = $7,
                    total_tokens = $8,
                    error = $9,
                    finished_at = now()
                WHERE id = $1
                """,
                run_id,
                status,
                output_ref,
                json_dump(evidence_ids or []),
                tool_call_count,
                input_tokens,
                output_tokens,
                total_tokens,
                error[:4000],
            )

    async def record_tool_call(
        self,
        *,
        agent_run_id: str,
        task_id: str,
        incident_group_id: str,
        tool_name: str,
        status: str,
        args: dict[str, Any] | None = None,
        result_ref: str = "",
        elapsed_ms: int = 0,
        error: str = "",
    ) -> str:
        tool_call_id = new_id("tc")
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO tool_calls (
                    id, agent_run_id, task_id, incident_group_id, tool_name,
                    status, args, result_ref, elapsed_ms, error, finished_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9, $10, now())
                """,
                tool_call_id,
                agent_run_id,
                task_id,
                incident_group_id,
                tool_name,
                status,
                json_dump(args or {}),
                result_ref,
                elapsed_ms,
                error[:4000],
            )
        return tool_call_id

    async def list_runs_for_task(self, task_id: str) -> list[dict[str, Any]]:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM agent_runs
                WHERE task_id = $1
                ORDER BY created_at DESC
                """,
                task_id,
            )
        return [_row_to_dict(row) or {} for row in rows]

    async def list_tool_calls_for_task(self, task_id: str) -> list[dict[str, Any]]:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM tool_calls
                WHERE task_id = $1
                ORDER BY created_at DESC
                """,
                task_id,
            )
        return [_row_to_dict(row) or {} for row in rows]


agent_run_repository = AgentRunRepository()

