"""Deep Diagnosis 图 (群聊 / M7)。

与 app/agents/graph.py 的 fast graph 并列存在, 不替代它。fast = 单 Agent
plan-execute-replan; deep = 确定性编排图 + 一组隔离的调查型专业 subagent。
"""

from app.diagnosis_graphs.deep_diagnosis_graph import build_deep_graph

__all__ = ["build_deep_graph"]
