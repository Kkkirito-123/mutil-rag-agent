"""基于 Redis 的接口限流 (改造文档第 8 步).

防止某个 IP / 来源 / API Key 高频打爆系统。实现固定窗口计数器:
    key = rate_limit:{scope}:{identity}:{window_bucket}
    INCR + (首次)EXPIRE; 超过 limit 即拒绝, 返回需要等待的秒数。

为什么用固定窗口而不是更精确的滑动窗口/令牌桶:
  - 实现简单、单次往返、足够挡住"刷接口"这类滥用;
  - 边界突刺 (窗口交界处瞬时 2x) 对运维平台可接受;
  - 需要更平滑可后续换 Lua 滑动窗口, 接口不变。

容错: fail-open —— Redis 不可用时直接放行, 不让限流器变成新的单点故障
(和 distributed_limiter 一致的取舍)。
"""

from __future__ import annotations

import time
from typing import Any, Optional

from fastapi import HTTPException, Request
from loguru import logger

from app.config import settings


async def _redis() -> Any | None:
    if not settings.rate_limit_enabled:
        return None
    try:
        from app.queue.redis_streams import incident_queue
        return await incident_queue.client()
    except Exception as exc:  # pragma: no cover
        logger.warning(f"[ratelimit] Redis 不可达, 限流降级放行: {type(exc).__name__}: {exc}")
        return None


def client_ip(request: Request) -> str:
    """取调用方 IP, 优先 X-Forwarded-For (反代后), 回落 request.client。"""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def hit(scope: str, identity: str, limit: int, window_sec: int) -> tuple[bool, int]:
    """记一次访问。返回 (是否放行, 建议 retry_after 秒)。

    放行: (True, 0); 超限: (False, 本窗口剩余秒数)。
    """
    client = await _redis()
    if client is None or limit <= 0:
        return True, 0
    now = int(time.time())
    bucket = now // window_sec
    key = f"rate_limit:{scope}:{identity}:{bucket}"
    try:
        count = await client.incr(key)
        if count == 1:
            await client.expire(key, window_sec)
        if int(count) > limit:
            retry_after = window_sec - (now % window_sec)
            return False, max(1, retry_after)
        return True, 0
    except Exception as exc:
        logger.warning(f"[ratelimit] 计数失败, 放行 scope={scope}: {type(exc).__name__}: {exc}")
        return True, 0


def _raise_429(retry_after: int, detail: str = "请求过于频繁，请稍后再试") -> None:
    raise HTTPException(
        status_code=429,
        detail={"error": "rate_limited", "message": detail, "retry_after": retry_after},
        headers={"Retry-After": str(retry_after)},
    )


async def enforce(scope: str, identity: str, limit: int, window_sec: int, detail: Optional[str] = None) -> None:
    """检查并在超限时直接抛 429 (供 FastAPI 接口内调用)。"""
    ok, retry_after = await hit(scope, identity, limit, window_sec)
    if not ok:
        logger.info(f"[ratelimit] blocked scope={scope} id={identity} limit={limit}/{window_sec}s")
        _raise_429(retry_after, detail or "请求过于频繁，请稍后再试")
