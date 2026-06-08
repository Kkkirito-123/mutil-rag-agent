"""AIOps diagnosis streaming service for the frontend API.

The service layer owns HTTP/SSE-facing concerns such as concurrency admission
and short-term report cache. The actual graph execution lives in
app.orchestration.diagnosis_runner so workers can reuse the same runtime
without depending on this SSE service.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from loguru import logger

from app.config import settings
from app.core.distributed_limiter import DistributedLimitBusy, distributed_slot
from app.orchestration.diagnosis_runner import make_event, run_diagnosis_graph
from app.incidents.models import DiagnosisMode


async def stream_diagnose(
    query: str,
    *,
    session_id: str = "default",
    diagnosis_mode: str | DiagnosisMode = DiagnosisMode.FAST,
) -> AsyncIterator[dict[str, Any]]:
    """Stream diagnosis events for the manual AIOps page.

    并发准入升级 (改造文档第 1 步): 用 Redis 分布式并发槽替代进程内 asyncio.Semaphore,
    多个 uvicorn worker 共享同一个全局上限 (manual_diagnosis_concurrency), 不再被进程数放大。
    满了仍是 "立刻拒绝 + 提示" (同步 SSE 入口不阻塞); 想排队的用 /aiops/diagnose/submit。
    """
    try:
        async with distributed_slot(
            "manual_diagnosis",
            limit=settings.manual_diagnosis_concurrency,
            ttl_seconds=settings.limiter_default_ttl_sec,
            refresh_interval_seconds=settings.limiter_default_refresh_sec,
            wait=False,
        ):
            try:
                async for event in run_diagnosis_graph(
                    query,
                    session_id=session_id,
                    diagnosis_mode=diagnosis_mode,
                    cache_reports=True,
                ):
                    yield event
            except asyncio.CancelledError:
                logger.info(f"[aiops] session={session_id} | 客户端断开")
                raise
            except Exception as exc:
                logger.exception(f"[aiops] session={session_id} | 诊断异常: {exc}")
                yield make_event(
                    "error",
                    "diagnosis_failed",
                    message=f"诊断失败: {type(exc).__name__}: {exc}",
                    error_type=type(exc).__name__,
                )
    except DistributedLimitBusy:
        logger.warning(f"[aiops] session={session_id} | 并发已满 (分布式槽)")
        yield make_event(
            "error",
            "concurrency_limited",
            message="当前诊断任务较多，请稍后重试，或改用『提交排队』(/aiops/diagnose/submit)",
            max_concurrency=settings.manual_diagnosis_concurrency,
        )
