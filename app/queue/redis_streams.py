"""Redis Streams queue for diagnosis tasks."""

from __future__ import annotations

import json
from typing import Any

from loguru import logger

from app.config import settings

# 优先级级别 (高 → 低). Worker 按这个顺序消费, critical 永远先于 low.
PRIORITY_LEVELS = ["critical", "high", "normal", "low"]


def level_for_severity(severity: str) -> str:
    """把告警 severity 映射到队列优先级 level (改造文档第 4 步规则)。"""
    s = str(severity or "").lower().strip()
    if s in {"critical", "page", "p0"}:
        return "critical"
    if s in {"high", "p1"}:
        return "high"
    if s in {"info", "low", "p3"}:
        return "low"
    # warning / p2 / 未知 → normal (手动诊断默认级别)
    return "normal"


def level_for_priority(priority: int) -> str:
    """没有 severity 时, 用旧的 priority 整数粗映射 (越小越紧急)。"""
    try:
        p = int(priority)
    except Exception:
        return "normal"
    if p <= 10:
        return "critical"
    if p <= 50:
        return "high"
    if p <= 100:
        return "normal"
    return "low"


class RedisIncidentQueue:
    """Small Redis Streams adapter with consumer-group support.

    这层只封装 Redis Streams 的队列语义, 不处理业务诊断。
    为什么这样拆:
    - Worker 只关心"拿任务/确认任务/放入死信队列";
    - 业务状态仍写 Postgres, Redis 只做运行态;
    - 后续要替换队列实现时, Worker 不需要改太多。
    """

    def __init__(self) -> None:
        self._client: Any | None = None

    async def connect(self) -> None:
        if self._client is not None:
            return
        try:
            from redis.asyncio import Redis
        except Exception as exc:  # pragma: no cover - dependency/runtime guard
            raise RuntimeError("redis 包不可用, 无法启用 Incident Queue") from exc

        block_timeout_sec = max(1.0, settings.diagnosis_worker_block_ms / 1000.0)
        self._client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=max(30.0, block_timeout_sec + 5.0),
            health_check_interval=30,
        )
        await self._client.ping()
        await self.ensure_group()
        logger.info(f"[incident-queue] connected stream={settings.incident_queue_stream}")

    async def close(self) -> None:
        if self._client is None:
            return
        await self._client.aclose()
        self._client = None
        logger.info("[incident-queue] closed")

    async def client(self) -> Any:
        if self._client is None:
            await self.connect()
        return self._client

    # ---- 优先级 stream 解析 ----
    def _base_stream(self) -> str:
        return settings.incident_queue_stream

    def _stream_for_level(self, level: str) -> str:
        """按 level 算出目标 stream 名。优先级关闭时所有 level 都落到单 base stream。"""
        if not settings.incident_queue_priority_enabled:
            return self._base_stream()
        lvl = level if level in PRIORITY_LEVELS else "normal"
        return f"{self._base_stream()}:{lvl}"

    def _consume_streams(self) -> list[str]:
        """Worker 消费的 stream 列表, 已按优先级从高到低排序。

        优先级开启时额外把 base stream 追加到最后, 兜底消费升级前/回落写入的旧消息。
        """
        if not settings.incident_queue_priority_enabled:
            return [self._base_stream()]
        streams = [f"{self._base_stream()}:{lvl}" for lvl in PRIORITY_LEVELS]
        streams.append(self._base_stream())  # 兼容旧消息
        return streams

    async def ensure_group(self) -> None:
        client = self._client
        if client is None:
            return
        # 在每条要消费的 stream 上创建同一个 consumer group (mkstream 自动建流)
        for stream in self._consume_streams():
            try:
                await client.xgroup_create(
                    name=stream,
                    groupname=settings.incident_queue_consumer_group,
                    id="0",
                    mkstream=True,
                )
            except Exception as exc:
                if "BUSYGROUP" not in str(exc):
                    raise

    async def enqueue_task(
        self,
        *,
        task_id: str,
        incident_group_id: str,
        incident_id: str,
        diagnosis_mode: str,
        priority: int,
        payload: dict[str, Any],
        level: str | None = None,
    ) -> str:
        client = await self.client()
        # level 优先用显式入参; 没传则从 payload.severity 或 priority 整数推断
        if level is None:
            severity = str((payload or {}).get("severity") or "")
            level = level_for_severity(severity) if severity else level_for_priority(priority)
        stream = self._stream_for_level(level)
        message_id = await client.xadd(
            stream,
            fields={
                "task_id": task_id,
                "incident_group_id": incident_group_id,
                "incident_id": incident_id,
                "diagnosis_mode": diagnosis_mode,
                "priority": str(priority),
                "level": level,
                "payload": json.dumps(payload or {}, ensure_ascii=False, default=str),
            },
            maxlen=settings.incident_queue_maxlen,
            approximate=True,
        )
        logger.info(
            f"[incident-queue] enqueued task={task_id} group={incident_group_id} "
            f"level={level} stream={stream} msg={message_id}"
        )
        return str(message_id)

    async def read_tasks(
        self,
        *,
        consumer_name: str,
        count: int = 1,
        block_ms: int | None = None,
    ) -> list[tuple[str, dict[str, Any]]]:
        """按优先级读取任务 (改造文档第 4 步)。

        策略:
          1) 非阻塞地按 critical→high→normal→low 顺序逐条 stream 读, 命中即返回 (严格插队);
          2) 全空时, 对所有 stream 做一次阻塞读 (block_ms), 醒来后下一轮再重新按优先级取。
        返回的 item 里带 __stream__, 便于后续 ack/DLQ 定位到正确的 stream。
        """
        client = await self.client()
        group = settings.incident_queue_consumer_group
        streams = self._consume_streams()
        block = block_ms if block_ms is not None else settings.diagnosis_worker_block_ms

        # 1) 非阻塞优先级 pass
        for stream in streams:
            rows = await client.xreadgroup(
                groupname=group,
                consumername=consumer_name,
                streams={stream: ">"},
                count=count,
                block=None,
            )
            tasks = self._parse_rows(rows)
            if tasks:
                return tasks

        # 2) 全空 → 一次性阻塞读所有 stream, 醒来即返回 (下一轮 loop 会重新按优先级取)
        try:
            rows = await client.xreadgroup(
                groupname=group,
                consumername=consumer_name,
                streams={s: ">" for s in streams},
                count=count,
                block=block,
            )
        except Exception as exc:
            if type(exc).__name__ == "TimeoutError":
                logger.warning(
                    f"[incident-queue] xreadgroup timeout after block={block}ms; treating as empty poll"
                )
                return []
            raise
        return self._parse_rows(rows)

    def _parse_rows(self, rows: Any) -> list[tuple[str, dict[str, Any]]]:
        """把 xreadgroup 返回解析成 (message_id, item) 列表, 并给 item 打上 __stream__。"""
        tasks: list[tuple[str, dict[str, Any]]] = []
        for stream_name, messages in rows or []:
            for message_id, fields in messages:
                item = self._decode_item(fields)
                item["__stream__"] = str(stream_name)
                tasks.append((str(message_id), item))
        return tasks

    async def claim_stale_tasks(
        self,
        *,
        consumer_name: str,
        min_idle_ms: int,
        count: int,
    ) -> list[tuple[str, dict[str, Any]]]:
        """Claim old pending messages that were delivered but not ACKed.

        为什么要加:
        - Redis Streams 的 consumer group 会把已投递但未 ACK 的消息放进 PEL
          (Pending Entries List)。
        - 如果 Worker 崩溃, 消息会一直留在 PEL, 新 Worker 用普通 XREADGROUP
          读不到它。
        - XAUTOCLAIM 会把空闲超过 min_idle_ms 的 pending 消息转给当前 Worker,
          让任务有机会继续执行。

        预期效果:
        - Worker 崩溃不会导致任务永久卡在 running/pending。
        - 多 Worker 部署时, 存活 Worker 可以接管旧任务。

        注意:
        - min_idle_ms 必须大于正常任务耗时, 否则长任务可能被重复认领。
        """
        client = await self.client()
        tasks: list[tuple[str, dict[str, Any]]] = []
        # 按优先级顺序在每条 stream 上回收 stale pending
        for stream in self._consume_streams():
            try:
                result = await client.xautoclaim(
                    stream,
                    settings.incident_queue_consumer_group,
                    consumer_name,
                    min_idle_ms,
                    start_id="0-0",
                    count=count,
                )
            except Exception as exc:
                logger.warning(
                    f"[incident-queue] xautoclaim failed stream={stream}: {type(exc).__name__}: {exc}"
                )
                continue

            messages = []
            # redis-py returns: (next_start_id, [(message_id, fields), ...], deleted_ids)
            if isinstance(result, (list, tuple)) and len(result) >= 2:
                messages = result[1] or []
            for message_id, fields in messages:
                item = self._decode_item(fields)
                item["__stream__"] = stream
                tasks.append((str(message_id), item))
            if tasks:
                break  # 已回收到高优先级 stream 的 stale, 本轮先处理这些
        if tasks:
            logger.warning(
                f"[incident-queue] claimed {len(tasks)} stale pending task(s) "
                f"consumer={consumer_name} min_idle_ms={min_idle_ms}"
            )
        return tasks

    async def ack(self, message_id: str, stream: str | None = None) -> None:
        client = await self.client()
        await client.xack(
            stream or self._base_stream(),
            settings.incident_queue_consumer_group,
            message_id,
        )

    async def dead_letter(
        self,
        *,
        message_id: str,
        item: dict[str, Any],
        reason: str,
    ) -> str:
        """Move a message to the dead-letter stream and ACK the original.

        为什么要加:
        - 格式损坏或超过最大重试次数的任务不能无限重试;
        - 也不能直接 ACK 丢弃, 否则后续无法定位原因;
        - DLQ 保存原始消息和失败原因, 供人工排查或离线重放。

        预期效果:
        - 主队列不会被 poison message 卡住;
        - 失败任务仍可追溯。
        """
        client = await self.client()
        dlq_id = await client.xadd(
            settings.incident_queue_dlq_stream,
            fields={
                "original_message_id": message_id,
                "reason": reason[:2000],
                "task_id": str(item.get("task_id") or ""),
                "incident_group_id": str(item.get("incident_group_id") or ""),
                "incident_id": str(item.get("incident_id") or ""),
                "diagnosis_mode": str(item.get("diagnosis_mode") or ""),
                "priority": str(item.get("priority") or ""),
                "payload": json.dumps(item.get("payload") or {}, ensure_ascii=False, default=str),
                "raw_item": json.dumps(item or {}, ensure_ascii=False, default=str),
            },
            maxlen=settings.incident_queue_maxlen,
            approximate=True,
        )
        # ack 原消息要落到它真正所在的 stream (优先级队列下不是 base stream)
        await self.ack(message_id, stream=item.get("__stream__"))
        logger.warning(
            f"[incident-queue] dead-lettered msg={message_id} dlq={dlq_id} reason={reason[:120]}"
        )
        return str(dlq_id)

    async def status(self) -> dict[str, Any]:
        """采集主队列 + DLQ + consumer group 的运行态快照, 供 /api/v1/queue/status 使用.

        为什么集中在 adapter 里:
        - Redis 命令 (XLEN / XINFO / XPENDING) 都是 Stream 专属;
        - 业务层 (API / 前端) 只关心结构化字段 (depth / pending / workers / dlq);
        - 任何 Redis 异常这里吞掉, 顶层 API 仍能返回 partial 数据 + error_hint.
        """
        out: dict[str, Any] = {
            "configured": True,
            "stream": settings.incident_queue_stream,
            "consumer_group": settings.incident_queue_consumer_group,
            "dlq_stream": settings.incident_queue_dlq_stream,
            "depth": None,                # 真实 backlog: lag(未投递) + pending(已投递未 ACK)
            "pending": None,              # consumer group 已投递但未 ACK 数
            "lag": None,                  # consumer group 未投递给消费者的消息数
            "stream_length": None,        # Redis Stream 原始长度 (ACK 后不会立刻下降)
            "dlq_depth": None,            # 死信队列长度
            "workers": [],                # 每个 consumer 一行
            "warnings": [],
        }
        try:
            client = await self.client()
        except Exception as exc:
            out["configured"] = False
            out["warnings"].append(f"redis 不可达: {type(exc).__name__}: {exc}")
            return out

        async def _safe(coro, label: str):
            try:
                return await coro
            except Exception as exc:
                out["warnings"].append(f"{label} 失败: {type(exc).__name__}: {exc}")
                return None

        consume_streams = self._consume_streams()
        out["priority_enabled"] = settings.incident_queue_priority_enabled

        # 各优先级 stream 原始长度。注意 XLEN 是 stream 历史长度, ACK 后不会立刻下降,
        # 所以不能拿它当"待消费 backlog"; 真正 backlog 在下面用 XINFO GROUPS 的 lag+pending 算。
        total_stream_length = 0
        stream_length_by_level: dict[str, int] = {}
        for stream in consume_streams:
            n = await _safe(client.xlen(stream), f"xlen {stream}")
            if n is not None:
                total_stream_length += int(n)
                # 取 stream 名最后一段当 level 标签 (base stream 标 base)
                lvl = stream.rsplit(":", 1)[-1] if ":" in stream and stream != self._base_stream() else "base"
                stream_length_by_level[lvl] = int(n)
        out["stream_length"] = total_stream_length
        out["stream_length_by_level"] = stream_length_by_level
        out["dlq_depth"] = await _safe(client.xlen(settings.incident_queue_dlq_stream), "xlen dlq")

        # consumer group lag / pending + consumer 信息 (跨所有 stream 聚合)
        total_pending = 0
        total_lag = 0
        lag_known = True
        backlog_by_level: dict[str, int] = {}
        pending_by_level: dict[str, int] = {}
        lag_by_level: dict[str, int | None] = {}
        workers_by_name: dict[str, dict[str, Any]] = {}
        for stream in consume_streams:
            lvl = stream.rsplit(":", 1)[-1] if ":" in stream and stream != self._base_stream() else "base"
            stream_pending = 0
            stream_lag: int | None = None
            try:
                groups = await client.xinfo_groups(stream)
                for g in groups or []:
                    if g.get("name") == settings.incident_queue_consumer_group:
                        stream_pending = int(g.get("pending") or 0)
                        raw_lag = g.get("lag")
                        if raw_lag is not None:
                            stream_lag = int(raw_lag or 0)
                        else:
                            lag_known = False
                        break
            except Exception:
                lag_known = False
            total_pending += stream_pending
            if stream_lag is None:
                lag_by_level[lvl] = None
            else:
                total_lag += stream_lag
                lag_by_level[lvl] = stream_lag
            pending_by_level[lvl] = stream_pending
            backlog_by_level[lvl] = stream_pending + (stream_lag or 0)
            try:
                consumers = await client.xinfo_consumers(
                    stream, settings.incident_queue_consumer_group
                )
                for c in consumers or []:
                    name = c.get("name", "")
                    w = workers_by_name.setdefault(name, {"name": name, "pending": 0, "idle_ms": c.get("idle", 0), "alive": False})
                    w["pending"] += int(c.get("pending", 0) or 0)
                    w["idle_ms"] = min(w["idle_ms"], c.get("idle", 0)) if w["idle_ms"] else c.get("idle", 0)
            except Exception:
                pass
        out["pending"] = total_pending
        out["pending_by_level"] = pending_by_level
        out["lag"] = total_lag if lag_known else None
        out["lag_by_level"] = lag_by_level
        out["depth"] = (total_pending + total_lag) if lag_known else total_pending
        out["depth_by_level"] = backlog_by_level

        for name, w in workers_by_name.items():
            heartbeat_key = (
                f"aiops:worker:{settings.incident_queue_consumer_group}:{name}:heartbeat"
            )
            try:
                w["alive"] = (await client.exists(heartbeat_key)) > 0
            except Exception:
                pass
            out["workers"].append(w)

        out["alive_workers"] = sum(1 for w in out["workers"] if w.get("alive"))
        return out

    async def heartbeat(self, consumer_name: str) -> None:
        """Write a short-lived heartbeat key for this Worker.

        为什么要加:
        - Redis Streams 能告诉我们消息是否 pending, 但不能直接告诉我们某个
          Worker 进程是否还活着;
        - heartbeat key 带 TTL, 正常 Worker 会定期刷新;
        - 运维或后续 supervisor 可以通过 key 是否过期判断 Worker 是否离线。

        预期效果:
        - 能观察 Worker 存活状态;
        - 后续可以基于 heartbeat 做更精细的调度和告警。
        """
        client = await self.client()
        key = (
            f"aiops:worker:{settings.incident_queue_consumer_group}:"
            f"{consumer_name}:heartbeat"
        )
        await client.set(key, "1", ex=settings.diagnosis_worker_heartbeat_ttl_sec)

    @staticmethod
    def _decode_item(fields: dict[str, Any]) -> dict[str, Any]:
        item = dict(fields or {})
        raw_payload = item.get("payload") or "{}"
        try:
            item["payload"] = json.loads(raw_payload) if isinstance(raw_payload, str) else raw_payload
        except Exception:
            item["payload"] = {}
        return item


incident_queue = RedisIncidentQueue()
