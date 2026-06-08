"""Redis 分布式并发槽 (跨进程/跨 Uvicorn worker 的全局限流).

为什么需要:
  - 原来的 asyncio.Semaphore 只在单个 Python 进程内有效;
  - 一旦 `uvicorn app.main:app --workers 4`, 每个进程各有一份 Semaphore,
    总并发会被放大 4 倍, 失去保护意义;
  - 用 Redis 做"全局槽位", 所有 API/Worker 进程共享同一个上限.

实现要点 (对应改造文档第 1 步):
  - 每种资源一个 Redis ZSET: aiops:limiter:{resource}
      member = 唯一 token (host:pid:uuid), score = 过期时间(ms);
  - Lua 脚本原子完成 "清过期 → 数当前 → 没满则占一个槽" (避免 check-then-act 竞态);
  - TTL: 进程崩溃没来得及释放时, 槽位到期被自动清掉, 不会永久泄漏;
  - 心跳续期: 长任务运行期间定期把自己 token 的 score 往后推, 防止被误清;
  - finally 自动 ZREM 释放;
  - contextvar 暴露当前槽句柄, 供"等待人工审批时先把槽让出去"用 (pause/resume).

容错策略: fail-open. Redis 不可用时 acquire 直接放行并打 warning ——
  这个项目的队列本来就强依赖 Redis, 真挂了整条链路都不工作, 限流层没必要再叠一层
  硬失败把诊断也拖死; 宁可短暂失去全局上限, 也不让限流器成为新的单点故障.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import socket
import time
import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any, AsyncIterator, Optional

from loguru import logger

from app.config import settings


class DistributedLimitBusy(Exception):
    """资源槽已满且未启用等待时抛出 (调用方据此返回 '请稍后重试' / 入队)。"""

    def __init__(self, resource: str, limit: int) -> None:
        self.resource = resource
        self.limit = limit
        super().__init__(f"资源 {resource!r} 并发已满 (limit={limit})")


# ---- Lua: 原子抢槽 ----
# KEYS[1]=zset  ARGV[1]=limit  ARGV[2]=ttl_ms  ARGV[3]=token
# 用 redis 服务端 TIME 取当前时间, 避免各客户端时钟漂移.
_ACQUIRE_LUA = """
local t = redis.call('TIME')
local now_ms = tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000)
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now_ms)
local count = redis.call('ZCARD', KEYS[1])
if count < tonumber(ARGV[1]) then
  redis.call('ZADD', KEYS[1], now_ms + tonumber(ARGV[2]), ARGV[3])
  redis.call('PEXPIRE', KEYS[1], tonumber(ARGV[2]) * 2)
  return 1
end
return 0
"""

# ---- Lua: 心跳续期 (只在 token 还在时更新它的 score) ----
_REFRESH_LUA = """
local t = redis.call('TIME')
local now_ms = tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000)
if redis.call('ZSCORE', KEYS[1], ARGV[2]) then
  redis.call('ZADD', KEYS[1], now_ms + tonumber(ARGV[1]), ARGV[2])
  redis.call('PEXPIRE', KEYS[1], tonumber(ARGV[1]) * 2)
  return 1
end
return 0
"""


def _key(resource: str) -> str:
    return f"{settings.limiter_key_prefix}:{resource}"


def _new_token() -> str:
    return f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:12]}"


async def _redis() -> Any | None:
    """复用 incident_queue 的 Redis 连接, 避免再开一个连接池。Redis 不可用返回 None。"""
    if not settings.distributed_limiter_enabled:
        return None
    try:
        from app.queue.redis_streams import incident_queue
        return await incident_queue.client()
    except Exception as exc:  # pragma: no cover - 防御式
        logger.warning(f"[limiter] Redis 不可达, 限流降级放行: {type(exc).__name__}: {exc}")
        return None


async def try_acquire_slot(resource: str, limit: int, ttl_seconds: int) -> Optional[str]:
    """非阻塞抢一个槽。成功返回 token, 满了返回 None。Redis 不可用时返回特殊放行 token。"""
    client = await _redis()
    if client is None:
        return "__fail_open__"
    token = _new_token()
    try:
        ok = await client.eval(_ACQUIRE_LUA, 1, _key(resource), str(limit), str(int(ttl_seconds * 1000)), token)
        return token if int(ok) == 1 else None
    except Exception as exc:
        logger.warning(f"[limiter] acquire 失败, 降级放行 resource={resource}: {type(exc).__name__}: {exc}")
        return "__fail_open__"


async def _refresh_slot(resource: str, token: str, ttl_seconds: int) -> bool:
    if token == "__fail_open__":
        return True
    client = await _redis()
    if client is None:
        return True
    try:
        ok = await client.eval(_REFRESH_LUA, 1, _key(resource), str(int(ttl_seconds * 1000)), token)
        return int(ok) == 1
    except Exception:
        return False


async def release_slot(resource: str, token: str) -> None:
    if token == "__fail_open__":
        return
    client = await _redis()
    if client is None:
        return
    with contextlib.suppress(Exception):
        await client.zrem(_key(resource), token)


async def slot_usage(resource: str) -> Optional[int]:
    """当前占用数 (清掉过期后), 给 /queue/status 之类做可观测。Redis 不可用返回 None。"""
    client = await _redis()
    if client is None:
        return None
    try:
        await client.zremrangebyscore(_key(resource), "-inf", int(time.time() * 1000))
        return int(await client.zcard(_key(resource)))
    except Exception:
        return None


class SlotHandle:
    """已持有的槽句柄。支持在等待人工审批等长阻塞时 pause(让出) / resume(重抢)。"""

    def __init__(self, resource: str, token: str, limit: int, ttl_seconds: int, refresh_interval: int) -> None:
        self.resource = resource
        self.token = token
        self.limit = limit
        self.ttl_seconds = ttl_seconds
        self.refresh_interval = refresh_interval
        self._hb: asyncio.Task[None] | None = None
        self._paused = False

    def start_heartbeat(self) -> None:
        if self.token == "__fail_open__":
            return
        self._hb = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self) -> None:
        while True:
            await asyncio.sleep(self.refresh_interval)
            await _refresh_slot(self.resource, self.token, self.ttl_seconds)

    async def _stop_heartbeat(self) -> None:
        if self._hb:
            self._hb.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._hb
            self._hb = None

    async def pause(self) -> None:
        """让出槽位 (停心跳 + 释放), 用于进入人工审批等不确定时长的等待, 避免空占并发。"""
        if self._paused or self.token == "__fail_open__":
            return
        self._paused = True
        await self._stop_heartbeat()
        await release_slot(self.resource, self.token)
        logger.info(f"[limiter] slot paused resource={self.resource} (让出并发槽, 等待人工审批)")

    async def resume(self) -> None:
        """审批结束后重新抢回槽位 (满了则等待), 恢复执行。"""
        if not self._paused or self.token == "__fail_open__":
            return
        self.token = _new_token()
        while True:
            tok = await try_acquire_slot(self.resource, self.limit, self.ttl_seconds)
            if tok is not None:
                self.token = tok
                break
            await asyncio.sleep(0.5)
        self._paused = False
        self.start_heartbeat()
        logger.info(f"[limiter] slot resumed resource={self.resource}")

    async def close(self) -> None:
        await self._stop_heartbeat()
        if not self._paused:
            await release_slot(self.resource, self.token)


# 当前协程持有的槽 (供 tool_runner 在审批等待时 pause/resume)
current_slot: ContextVar[Optional[SlotHandle]] = ContextVar("current_slot", default=None)


@asynccontextmanager
async def distributed_slot(
    resource: str,
    *,
    limit: int,
    ttl_seconds: int = 90,
    refresh_interval_seconds: int = 30,
    wait: bool = False,
    wait_timeout_seconds: float | None = None,
    poll_interval_seconds: float = 0.5,
) -> AsyncIterator[SlotHandle]:
    """分布式并发槽上下文管理器。

    wait=False: 抢不到立刻抛 DistributedLimitBusy (用于 "满了就拒绝/入队" 的同步入口)。
    wait=True:  抢不到就轮询等待 (用于 Worker: 尊重全局并发, 满了排队等)。
    """
    token = await try_acquire_slot(resource, limit, ttl_seconds)
    if token is None:
        if not wait:
            raise DistributedLimitBusy(resource, limit)
        deadline = (time.monotonic() + wait_timeout_seconds) if wait_timeout_seconds else None
        while token is None:
            await asyncio.sleep(poll_interval_seconds)
            if deadline is not None and time.monotonic() > deadline:
                raise DistributedLimitBusy(resource, limit)
            token = await try_acquire_slot(resource, limit, ttl_seconds)

    handle = SlotHandle(resource, token, limit, ttl_seconds, refresh_interval_seconds)
    handle.start_heartbeat()
    ctx_token = current_slot.set(handle)
    try:
        yield handle
    finally:
        current_slot.reset(ctx_token)
        await handle.close()
