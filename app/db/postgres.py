"""Postgres connection and schema bootstrap.

This module is intentionally small and explicit. The first framework upgrade
needs a durable incident ledger more than a full ORM layer.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.config import settings

_pool: Any | None = None
_SCHEMA_LOCK_KEY = 990001


async def connect_postgres() -> None:
    """Create the global asyncpg pool."""
    global _pool
    if _pool is not None:
        return

    try:
        import asyncpg
    except Exception as exc:  # pragma: no cover - dependency/runtime guard
        raise RuntimeError(
            "asyncpg 未安装, 无法启用 Incident Pipeline. 请先 pip install -r requirements.txt"
        ) from exc

    _pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=settings.database_pool_min_size,
        max_size=settings.database_pool_max_size,
        command_timeout=30,
    )
    logger.info("[postgres] connected")


async def close_postgres() -> None:
    """Close the global asyncpg pool."""
    global _pool
    if _pool is None:
        return
    await _pool.close()
    _pool = None
    logger.info("[postgres] closed")


async def get_pool() -> Any:
    """Return the global pool, creating it lazily if needed."""
    if _pool is None:
        await connect_postgres()
    return _pool


async def init_incident_schema() -> None:
    """Create the Incident Pipeline tables if they do not exist."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # 多 uvicorn worker / 多 diagnosis worker 会同时执行 lifespan。DDL 即使带
        # IF NOT EXISTS, 并发 ALTER/CREATE INDEX 仍可能在 Postgres 里互相死锁。
        # 用 advisory lock 把 schema bootstrap 串行化; 只影响启动时, 不影响请求路径。
        await conn.execute("SELECT pg_advisory_lock($1)", _SCHEMA_LOCK_KEY)
        try:
            await conn.execute(_SCHEMA_SQL)
        finally:
            await conn.execute("SELECT pg_advisory_unlock($1)", _SCHEMA_LOCK_KEY)
    logger.info("[postgres] incident schema ready")


async def postgres_health() -> bool:
    """Return True when Postgres is reachable."""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            value = await conn.fetchval("select 1")
        return value == 1
    except Exception as exc:
        logger.warning(f"[postgres] health check failed: {type(exc).__name__}: {exc}")
        return False


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    fingerprint TEXT NOT NULL,
    status TEXT NOT NULL,
    alertname TEXT NOT NULL,
    severity TEXT NOT NULL,
    service TEXT NOT NULL DEFAULT '',
    instance TEXT NOT NULL DEFAULT '',
    receiver TEXT NOT NULL DEFAULT '',
    group_key TEXT NOT NULL DEFAULT '',
    labels JSONB NOT NULL DEFAULT '{}'::jsonb,
    annotations JSONB NOT NULL DEFAULT '{}'::jsonb,
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    query TEXT NOT NULL DEFAULT '',
    starts_at TIMESTAMPTZ,
    ends_at TIMESTAMPTZ,
    first_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
    seen_count INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_alerts_fingerprint ON alerts(fingerprint);
CREATE INDEX IF NOT EXISTS idx_alerts_status_last_seen ON alerts(status, last_seen DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_service_last_seen ON alerts(service, last_seen DESC);

CREATE TABLE IF NOT EXISTS incident_groups (
    id TEXT PRIMARY KEY,
    correlation_key TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'open',
    severity TEXT NOT NULL DEFAULT 'warning',
    primary_service TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    labels JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    alert_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_incident_groups_status_updated ON incident_groups(status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_incident_groups_service_updated ON incident_groups(primary_service, updated_at DESC);

CREATE TABLE IF NOT EXISTS incidents (
    id TEXT PRIMARY KEY,
    incident_group_id TEXT NOT NULL REFERENCES incident_groups(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'open',
    title TEXT NOT NULL DEFAULT '',
    severity TEXT NOT NULL DEFAULT 'warning',
    service TEXT NOT NULL DEFAULT '',
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_incidents_group ON incidents(incident_group_id);

CREATE TABLE IF NOT EXISTS incident_group_alerts (
    incident_group_id TEXT NOT NULL REFERENCES incident_groups(id) ON DELETE CASCADE,
    alert_id TEXT NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (incident_group_id, alert_id)
);

CREATE TABLE IF NOT EXISTS diagnosis_tasks (
    id TEXT PRIMARY KEY,
    incident_group_id TEXT NOT NULL REFERENCES incident_groups(id) ON DELETE CASCADE,
    incident_id TEXT NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending',
    priority INTEGER NOT NULL DEFAULT 100,
    diagnosis_mode TEXT NOT NULL DEFAULT 'fast',
    queue_message_id TEXT NOT NULL DEFAULT '',
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    error TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    claimed_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_diagnosis_tasks_status_created ON diagnosis_tasks(status, created_at);
CREATE INDEX IF NOT EXISTS idx_diagnosis_tasks_group_status ON diagnosis_tasks(incident_group_id, status);

-- 去重幂等 (改造文档第 7 步): 用 DB 层唯一约束替代 Python SELECT-then-INSERT 竞态.
-- 相同 dedup_key 在 "活跃" 状态 (pending/running) 下只允许存在一条, 由部分唯一索引保证.
-- 老库平滑升级: 字段用 ADD COLUMN IF NOT EXISTS, 索引用 CREATE INDEX IF NOT EXISTS.
ALTER TABLE diagnosis_tasks ADD COLUMN IF NOT EXISTS dedup_key TEXT;
ALTER TABLE diagnosis_tasks ADD COLUMN IF NOT EXISTS repeat_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE diagnosis_tasks ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ;
CREATE UNIQUE INDEX IF NOT EXISTS idx_diagnosis_task_dedup_active
    ON diagnosis_tasks(dedup_key)
    WHERE status IN ('pending', 'running');

CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    incident_group_id TEXT NOT NULL REFERENCES incident_groups(id) ON DELETE CASCADE,
    incident_id TEXT REFERENCES incidents(id) ON DELETE SET NULL,
    source TEXT NOT NULL,
    type TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    content JSONB NOT NULL DEFAULT '{}'::jsonb,
    score DOUBLE PRECISION,
    occurred_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_evidence_incident_source ON evidence(incident_group_id, source, created_at DESC);

CREATE TABLE IF NOT EXISTS agent_runs (
    id TEXT PRIMARY KEY,
    task_id TEXT REFERENCES diagnosis_tasks(id) ON DELETE SET NULL,
    incident_group_id TEXT NOT NULL REFERENCES incident_groups(id) ON DELETE CASCADE,
    incident_id TEXT REFERENCES incidents(id) ON DELETE SET NULL,
    agent_name TEXT NOT NULL,
    agent_version TEXT NOT NULL DEFAULT 'v1',
    status TEXT NOT NULL DEFAULT 'pending',
    input_ref TEXT NOT NULL DEFAULT '',
    output_ref TEXT NOT NULL DEFAULT '',
    evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    tool_call_count INTEGER NOT NULL DEFAULT 0,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    error TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_task_agent ON agent_runs(task_id, agent_name);

CREATE TABLE IF NOT EXISTS tool_calls (
    id TEXT PRIMARY KEY,
    agent_run_id TEXT REFERENCES agent_runs(id) ON DELETE SET NULL,
    task_id TEXT REFERENCES diagnosis_tasks(id) ON DELETE SET NULL,
    incident_group_id TEXT REFERENCES incident_groups(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    args JSONB NOT NULL DEFAULT '{}'::jsonb,
    result_ref TEXT NOT NULL DEFAULT '',
    elapsed_ms INTEGER NOT NULL DEFAULT 0,
    error TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_tool_calls_task_created ON tool_calls(task_id, created_at DESC);

-- ============================================================
-- 审批请求 (ASK_DESTRUCTIVE 模式人工确认通道)
-- ============================================================
-- 为什么独立成表:
--   - PermissionMode=ASK_DESTRUCTIVE 时, 写/通知工具需要人工 allow/deny;
--   - 决策必须能被审计追溯 (谁批的, 何时, 给哪个工具调用);
--   - tool_runner 在 ask 命中后写一条 pending 行, 然后轮询等结果, 超时回 deny.
CREATE TABLE IF NOT EXISTS approval_requests (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    incident_group_id TEXT,
    agent_run_id TEXT,
    tool_name TEXT NOT NULL,
    tool_args JSONB NOT NULL DEFAULT '{}'::jsonb,
    reason TEXT NOT NULL DEFAULT '',
    impact_summary TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',  -- pending / approved / denied / timeout / cancelled
    decided_by TEXT NOT NULL DEFAULT '',
    decision_reason TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    decided_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT now() + INTERVAL '5 minutes'
);

CREATE INDEX IF NOT EXISTS idx_approval_requests_status_created
    ON approval_requests(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_approval_requests_task
    ON approval_requests(task_id, created_at DESC);

-- 注: 经验沉淀已改为文件系统 LLM Wiki (data/wiki/, 见 app/wiki/), 不再用 Postgres 表。
"""
