"""Executor 流式事件旁路.

LangGraph graph.astream() 只产出节点级事件, Executor 内部 LLM 的 token 级流式
没有官方出口. 这里用 ContextVar + asyncio.Queue 把 token 从 tool_runner
外送给 diagnosis_runner, 让前端/Worker 能看到 Executor 正在生成文字并记录工具事件.

用法:
  - diagnosis_runner 在启动 graph.astream 前调 set_sink(queue), 然后把 graph.astream
    包成 Task (Task 自动复制当前 context, 所以 tool_runner 里 get_sink() 拿得到).
  - tool_runner 每次流式输出调 await emit({...}).
  - diagnosis_runner 主循环 merge 自己的 "node event" 和 queue 里的 "token event",
    统一 yield 给 SSE.

为什么放 app/runtime/ 而不是 app/agents/:
  本质是底层"事件总线"工具, 与 transitions / agent_harness 同层。原先放 agents/
  会和 runtime/tool_runner.py 互相 import, 形成 runtime <-> agents 真循环。
"""

from __future__ import annotations

import asyncio
from contextvars import ContextVar
from typing import Any, Dict, Optional

_sink_var: ContextVar[Optional["asyncio.Queue[Dict[str, Any]]"]] = ContextVar(
    "executor_stream_sink", default=None
)
_step_var: ContextVar[int] = ContextVar("executor_current_step", default=0)


def set_sink(queue: "asyncio.Queue[Dict[str, Any]]") -> None:
    _sink_var.set(queue)


def set_step(iteration: int) -> None:
    _step_var.set(iteration)


def get_step() -> int:
    return _step_var.get()


_miss_count = 0
_emit_count = 0


async def emit(event: Dict[str, Any]) -> None:
    """把事件推到 diagnosis_runner 的中转队列. 队列不存在或满了, 静默丢弃."""
    global _miss_count, _emit_count
    from loguru import logger  # 放函数内避免循环 import

    q = _sink_var.get()
    if q is None:
        _miss_count += 1
        # 前 5 次 + 每 20 次打一条, 避免日志爆炸
        if _miss_count <= 5 or _miss_count % 20 == 0:
            logger.warning(
                f"[stream_sink] ⚠ sink=None (miss #{_miss_count}) type={event.get('type')} "
                f"— ContextVar 没跨 LangGraph 任务传过来"
            )
        return
    event.setdefault("iteration", _step_var.get())
    try:
        q.put_nowait(event)
        _emit_count += 1
        if _emit_count <= 3 or _emit_count % 50 == 0:
            logger.info(
                f"[stream_sink] emit #{_emit_count} type={event.get('type')} "
                f"iter={event.get('iteration')} qsize={q.qsize()}"
            )
    except asyncio.QueueFull:
        logger.warning(f"[stream_sink] queue full, drop type={event.get('type')}")
