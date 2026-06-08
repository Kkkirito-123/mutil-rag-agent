"""诊断 Worker 入口。

启动方式:
    python -m app.diagnosis_worker

Worker 从 Redis Stream 消费诊断任务、跑当前的 AIOps 图、把任务生命周期状态记到 Postgres。
未来 Deep Diagnosis 升级只需替换下层图实现, 入队/审计链路无需改动。
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import os
from typing import Any

from loguru import logger

from app.orchestration.audit import run_legacy_langgraph_with_audit
from app.config import settings
from app.core.distributed_limiter import distributed_slot
from app.core.mcp_client import mcp_client_manager
from app.db.postgres import close_postgres, connect_postgres, init_incident_schema
from app.incidents.repository import incident_repository
from app.queue.redis_streams import incident_queue


class DiagnosisWorker:
    """诊断任务的 Redis Streams 消费者。

    这个 Worker 的目标不是"跑得越快越好", 而是"失败后可恢复"。
    新手理解重点:
    - Redis Stream 负责把任务交给某个 Worker;
    - Postgres 负责记录任务事实状态;
    - Worker 成功后 ACK, 失败后根据 attempts 决定 retry 或 DLQ;
    - heartbeat 只是运行态信号, 不当事实库。
    """

    def __init__(self, consumer_name: str | None = None) -> None:
        suffix = os.environ.get("DIAGNOSIS_WORKER_ID") or settings.diagnosis_worker_consumer_name
        self.consumer_name = consumer_name or suffix
        self._stopping = asyncio.Event()
        self._heartbeat_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        await connect_postgres()
        await init_incident_schema()
        await incident_queue.connect()
        await mcp_client_manager.connect(fail_silently=True)
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info(f"[diagnosis-worker] started consumer={self.consumer_name}")

        while not self._stopping.is_set():
            # 先尝试回收 stale pending 任务, 再读新任务。
            # 为什么放在这里:
            # - 普通 XREADGROUP 只读新消息, 不会自动处理崩溃 Worker 留下的 pending;
            # - 每轮先 reclaim, 可以让旧任务恢复执行。
            tasks = await self._claim_stale_tasks_once()
            if not tasks:
                tasks = await incident_queue.read_tasks(
                    consumer_name=self.consumer_name,
                    count=1,
                    block_ms=settings.diagnosis_worker_block_ms,
                )
            if not tasks:
                continue
            for message_id, item in tasks:
                await self.handle_message(message_id, item)

    async def stop(self) -> None:
        self._stopping.set()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._heartbeat_task
        await mcp_client_manager.close()
        await incident_queue.close()
        await close_postgres()

    async def handle_message(self, message_id: str, item: dict[str, Any]) -> None:
        task_id = str(item.get("task_id") or "")
        if not task_id:
            logger.warning(f"[diagnosis-worker] message={message_id} missing task_id, DLQ")
            await incident_queue.dead_letter(
                message_id=message_id,
                item=item,
                reason="message missing task_id",
            )
            return

        task = await incident_repository.get_task(task_id)
        if task is None:
            await incident_queue.dead_letter(
                message_id=message_id,
                item=item,
                reason=f"task {task_id} not found in Postgres",
            )
            return

        if str(task.get("status") or "") == "succeeded":
            # 幂等保护: Redis 里可能有重复消息, 但 Postgres 已经表明任务完成。
            # 这种情况直接 ACK, 不重复跑诊断, 避免重复写 Evidence。
            logger.info(f"[diagnosis-worker] task={task_id} already succeeded, ack duplicate")
            await incident_queue.ack(message_id, stream=item.get("__stream__"))
            return

        attempts = int(task.get("attempts") or 0)
        max_attempts = int(task.get("max_attempts") or settings.diagnosis_task_max_attempts)
        if attempts >= max_attempts:
            await incident_repository.mark_task_failed(
                task_id,
                f"max attempts exhausted before run: attempts={attempts}, max={max_attempts}",
            )
            await incident_queue.dead_letter(
                message_id=message_id,
                item=item,
                reason=f"max attempts exhausted before run: attempts={attempts}, max={max_attempts}",
            )
            return

        logger.info(f"[diagnosis-worker] task={task_id} message={message_id} running")
        try:
            await incident_repository.mark_task_running(task_id)
            # 为什么加 timeout:
            # - LLM/MCP/网络工具都有可能长时间不返回;
            # - 没有 timeout 时, 一个坏任务会永久占住 Worker;
            # - timeout 后走 retry/DLQ, 系统能继续消费后续任务。
            #
            # 并发槽 (改造文档第 1/3 步): 所有 Worker 副本共享 worker_diagnosis 全局上限。
            # wait=True 表示槽满了就等 (而不是超跑), 保证无论起多少个 Worker, 同时真正
            # 在跑的诊断不超过 worker_diagnosis_concurrency。心跳续期防长任务被误回收。
            async with distributed_slot(
                "worker_diagnosis",
                limit=settings.worker_diagnosis_concurrency,
                ttl_seconds=settings.limiter_default_ttl_sec,
                refresh_interval_seconds=settings.limiter_default_refresh_sec,
                wait=True,
            ):
                result = await asyncio.wait_for(
                    run_legacy_langgraph_with_audit(task_id, item),
                    timeout=settings.diagnosis_task_timeout_sec,
                )
            await incident_repository.mark_task_succeeded(
                task_id,
                report=result.report,
                agent_run_id=result.agent_run_id,
                evidence_ids=result.evidence_ids,
            )
            await incident_queue.ack(message_id, stream=item.get("__stream__"))
            logger.info(
                f"[diagnosis-worker] task={task_id} succeeded "
                f"run={result.agent_run_id} evidence={len(result.evidence_ids)} "
                f"tools={result.tool_call_count}"
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            await self._handle_failure(message_id, item, task_id, exc)

    async def _handle_failure(
        self,
        message_id: str,
        item: dict[str, Any],
        task_id: str,
        exc: Exception,
    ) -> None:
        """决定失败任务该 retry 还是进 DLQ。"""
        error = f"{type(exc).__name__}: {exc}"
        logger.exception(f"[diagnosis-worker] task={task_id} failed: {error}")

        task = await incident_repository.get_task(task_id)
        attempts = int((task or {}).get("attempts") or 0)
        max_attempts = int((task or {}).get("max_attempts") or settings.diagnosis_task_max_attempts)

        if attempts >= max_attempts:
            # 为什么失败到上限要进 DLQ:
            # - 继续重试只会浪费 LLM/MCP/数据库资源;
            # - DLQ 保留原始消息和错误原因, 便于之后人工分析或重放。
            await incident_repository.mark_task_failed(task_id, error)
            await incident_queue.dead_letter(
                message_id=message_id,
                item=item,
                reason=f"attempts exhausted ({attempts}/{max_attempts}): {error}",
            )
            return

        # 仍可重试: 先把 Postgres 状态改回 pending, 再重新 XADD 一条消息,
        # 最后 ACK 当前失败消息。这个顺序避免"状态显示 pending 但队列没消息"。
        await incident_repository.mark_task_retry_pending(task_id, error)
        new_message_id = await self._reenqueue_task(task_id, item, task or {})
        await incident_repository.set_task_queue_message(task_id, new_message_id)
        await incident_queue.ack(message_id, stream=item.get("__stream__"))
        logger.warning(
            f"[diagnosis-worker] task={task_id} retry scheduled "
            f"attempts={attempts}/{max_attempts} old_msg={message_id} new_msg={new_message_id}"
        )

    async def _reenqueue_task(
        self,
        task_id: str,
        item: dict[str, Any],
        task: dict[str, Any],
    ) -> str:
        """把同一个 task 重新投回 Redis Stream, 等下一轮 attempt。"""
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else None
        if payload is None:
            payload = task.get("payload") if isinstance(task.get("payload"), dict) else {}

        def _as_int(value: Any, default: int) -> int:
            try:
                return int(value)
            except Exception:
                return default

        return await incident_queue.enqueue_task(
            task_id=task_id,
            incident_group_id=str(
                item.get("incident_group_id")
                or task.get("incident_group_id")
                or ""
            ),
            incident_id=str(item.get("incident_id") or task.get("incident_id") or ""),
            diagnosis_mode=str(
                item.get("diagnosis_mode")
                or task.get("diagnosis_mode")
                or "fast"
            ),
            priority=_as_int(item.get("priority") or task.get("priority"), 100),
            payload=payload,
            level=item.get("level"),  # 重试保持原优先级, 不降级
        )

    async def _claim_stale_tasks_once(self) -> list[tuple[str, dict[str, Any]]]:
        """认领崩溃/超时 Worker 留下的 pending 任务 (XAUTOCLAIM 回收)。"""
        return await incident_queue.claim_stale_tasks(
            consumer_name=self.consumer_name,
            min_idle_ms=settings.diagnosis_worker_reclaim_idle_ms,
            count=settings.diagnosis_worker_reclaim_count,
        )

    async def _heartbeat_loop(self) -> None:
        """Worker 进程活着期间, 定期刷新 Redis 心跳 key (用于 stale 检测)。"""
        while not self._stopping.is_set():
            try:
                await incident_queue.heartbeat(self.consumer_name)
            except Exception as exc:
                logger.warning(
                    f"[diagnosis-worker] heartbeat failed: {type(exc).__name__}: {exc}"
                )
            await asyncio.sleep(settings.diagnosis_worker_heartbeat_interval_sec)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AIOps Diagnosis Worker")
    parser.add_argument(
        "--name",
        default=None,
        help="Worker consumer 名 (同一 consumer group 下需唯一). "
             "也可用环境变量 DIAGNOSIS_WORKER_CONSUMER_NAME / DIAGNOSIS_WORKER_ID.",
    )
    return parser.parse_args()


async def main(consumer_name: str | None = None) -> None:
    worker = DiagnosisWorker(consumer_name=consumer_name)
    try:
        await worker.start()
    finally:
        with contextlib.suppress(Exception):
            await worker.stop()


if __name__ == "__main__":
    args = _parse_args()
    # 优先级: --name > 环境变量 (DiagnosisWorker.__init__ 内已处理) > 配置默认
    asyncio.run(main(consumer_name=args.name))
