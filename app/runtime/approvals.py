"""审批请求仓储 + 等待决策 (ASK_DESTRUCTIVE 模式的人工确认通道).

工作流:
  1. tool_runner 命中 ask 后调 create_request → 写一行 pending 到 approval_requests
  2. 前端"审批" inbox 列出所有 pending, 用户点 allow/deny → POST /approvals/{id}/decide
  3. tool_runner 在 await wait_for_decision 里轮询 (默认 2s 一次), 拿到 approved/denied/timeout 后行动

为什么用轮询而不是 LISTEN/NOTIFY:
  - 简单可靠, 不依赖 asyncpg LISTEN session 长连;
  - 审批本身是低频事件 (一次诊断顶多几条), 轮询开销可忽略;
  - 后续真有性能问题再升级到 pg_notify / Redis pub-sub.

任何 Postgres 异常都会被外层 catch, 让 tool_runner 优雅降级到旧的 ask=deny.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from loguru import logger

from app.config import settings
from app.core.db_utils import json_dump, new_id
from app.db.postgres import get_pool


def _row_to_dict(row: Any | None) -> dict[str, Any] | None:
    if row is None:
        return None
    item = dict(row)
    for key in ("tool_args",):
        v = item.get(key)
        if isinstance(v, str):
            try:
                item[key] = json.loads(v)
            except Exception:
                pass
    return item


class ApprovalRepository:
    """裸 SQL + asyncpg, 同 incidents/repository.py 风格."""

    async def create_request(
        self,
        *,
        tool_name: str,
        tool_args: Dict[str, Any] | None = None,
        reason: str = "",
        impact_summary: str = "",
        task_id: str = "",
        incident_group_id: str = "",
        agent_run_id: str = "",
        expires_in_sec: Optional[int] = None,
    ) -> str:
        req_id = new_id("apv")
        expires = datetime.now(timezone.utc) + timedelta(
            seconds=expires_in_sec or settings.approvals_timeout_sec
        )
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO approval_requests (
                    id, task_id, incident_group_id, agent_run_id,
                    tool_name, tool_args, reason, impact_summary,
                    status, expires_at
                )
                VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8, 'pending', $9)
                """,
                req_id,
                task_id or None,
                incident_group_id or None,
                agent_run_id or None,
                tool_name,
                json_dump(tool_args or {}),
                reason[:2000],
                impact_summary[:2000],
                expires,
            )
        logger.info(
            f"[approvals] requested id={req_id} tool={tool_name} "
            f"task={task_id or '-'} expires_in={expires_in_sec or settings.approvals_timeout_sec}s"
        )
        return req_id

    async def get_request(self, req_id: str) -> dict[str, Any] | None:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM approval_requests WHERE id = $1",
                req_id,
            )
        return _row_to_dict(row)

    async def list_pending(self, *, limit: int = 50) -> List[dict[str, Any]]:
        """前端 inbox 拉这个: 待人工确认的请求, 按创建时间倒序."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM approval_requests
                WHERE status = 'pending' AND expires_at > now()
                ORDER BY created_at DESC
                LIMIT $1
                """,
                max(1, min(limit, 200)),
            )
        return [_row_to_dict(r) or {} for r in rows]

    async def list_recent(self, *, limit: int = 50) -> List[dict[str, Any]]:
        """历史: 含 approved/denied/timeout, 给审计页用."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM approval_requests
                ORDER BY created_at DESC
                LIMIT $1
                """,
                max(1, min(limit, 200)),
            )
        return [_row_to_dict(r) or {} for r in rows]

    async def decide(
        self,
        req_id: str,
        *,
        decision: str,
        decided_by: str = "",
        reason: str = "",
    ) -> dict[str, Any] | None:
        """前端 POST 调这个写入决策. 只允许 pending → approved/denied."""
        if decision not in ("approved", "denied", "cancelled"):
            raise ValueError(f"unknown decision: {decision!r}")
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE approval_requests
                SET status = $2,
                    decided_by = $3,
                    decision_reason = $4,
                    decided_at = now()
                WHERE id = $1 AND status = 'pending'
                RETURNING *
                """,
                req_id,
                decision,
                (decided_by or "")[:200],
                (reason or "")[:2000],
            )
        if row is None:
            logger.warning(f"[approvals] decide id={req_id} 失败: 不是 pending 或不存在")
            return None
        logger.info(f"[approvals] decided id={req_id} -> {decision} by={decided_by!r}")
        return _row_to_dict(row)

    async def wait_for_decision(
        self,
        req_id: str,
        *,
        timeout_sec: Optional[int] = None,
        poll_interval_sec: Optional[float] = None,
    ) -> str:
        """轮询等审批结果, 返回最终 status 字符串.

        返回值: 'approved' / 'denied' / 'timeout' / 'cancelled' / 'error'
        timeout 时会顺手把状态改成 timeout 写回 (方便审计).
        """
        deadline = asyncio.get_event_loop().time() + (
            timeout_sec or settings.approvals_timeout_sec
        )
        interval = poll_interval_sec or settings.approvals_poll_interval_sec
        while True:
            try:
                row = await self.get_request(req_id)
            except Exception as exc:
                logger.warning(f"[approvals] wait poll 失败 id={req_id}: {type(exc).__name__}: {exc}")
                return "error"
            if row is None:
                return "error"
            status = row.get("status") or "pending"
            if status != "pending":
                return status
            if asyncio.get_event_loop().time() >= deadline:
                # 超时: 顺手回写 status=timeout
                try:
                    pool = await get_pool()
                    async with pool.acquire() as conn:
                        await conn.execute(
                            """
                            UPDATE approval_requests
                            SET status='timeout', decided_at=now(),
                                decision_reason='auto: 超过 expires_at 仍未决策'
                            WHERE id=$1 AND status='pending'
                            """,
                            req_id,
                        )
                except Exception:
                    pass
                return "timeout"
            await asyncio.sleep(interval)


approval_repository = ApprovalRepository()
