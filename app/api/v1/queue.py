"""Incident Queue 状态 API (只读, 给前端事件中心展示队列水位)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.config import settings
from app.queue.redis_streams import incident_queue

router = APIRouter(prefix="/queue", tags=["queue"])


@router.get("/status", summary="诊断队列水位 / Worker 存活")
async def get_queue_status() -> dict[str, Any]:
    """暴露 Redis Streams 主队列 + DLQ + consumer 状态.

    前端事件中心顶部用这个画"队列深度 / 排队 / Worker 数"卡, 让 SRE 一眼看清
    任务是堵着还是消费正常. 配置未开启 Incident Pipeline 时返回 configured=false.
    """
    if not settings.incident_pipeline_enabled:
        return {
            "configured": False,
            "reason": "incident_pipeline_enabled=False, 队列未启用",
        }
    status = await incident_queue.status()
    # 附带分布式并发槽占用 (改造文档第 1/3/5 步), 让前端看到"并发打满没"
    try:
        from app.core.distributed_limiter import slot_usage
        status["slots"] = {
            "manual_diagnosis": {
                "used": await slot_usage("manual_diagnosis"),
                "limit": settings.manual_diagnosis_concurrency,
            },
            "worker_diagnosis": {
                "used": await slot_usage("worker_diagnosis"),
                "limit": settings.worker_diagnosis_concurrency,
            },
        }
    except Exception:
        pass
    return status
