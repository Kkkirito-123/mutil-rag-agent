"""LangGraph 主图入口。

Plan-Execute-Replan 三段式：
  Planner    -> 把告警拆为多步计划
  Executor   -> 执行单步, 调工具 (支持只读并行)
  Replanner  -> 看结果, 决定继续 / 替换计划 / 收尾

详细图结构见 graph.py, 状态见 state.py。
"""

from app.agents.state import PlanExecuteState


def build_aiops_graph():
    """懒加载 + 构建 fast 诊断图 (避免顶层 import 把 langchain 拖到模块加载期)。"""
    from app.agents.graph import build_aiops_graph as _build_aiops_graph

    return _build_aiops_graph()


__all__ = ["build_aiops_graph", "PlanExecuteState"]
