"""Deep Diagnosis (群聊 / 多 Agent 组诊断) 的共享状态。

与 fast 的 PlanExecuteState 分开: fast 是单 Agent plan-execute-replan, deep 是
"确定性编排图 + 一组隔离的调查型 subagent"。沿用 LangGraph reducer 约定:
  - 普通字段 = 覆盖;
  - Annotated[List, operator.add] = 累加 (并行专业 Agent 并发写 evidences 靠它做并发安全归并)。

注意: 本文件**不要**加 `from __future__ import annotations` —— 否则 Annotated 元数据会被
字符串化, LangGraph 读不到 operator.add reducer。这与 app/agents/state.py 的处理一致。

设计取舍 (借鉴 learn-claude-code 课程 s06/s15, 见 COURSE_SUMMARY.md):
  - 专业 Agent 是"一次性、隔离上下文、只回 Evidence(=summary)"的 subagent (s06),
    不是持久互聊的 teammate (s15)。所以这里没有 inbox / request_id / 协议字段,
    只有一个并发安全的 evidences 累加器。
  - 各 Agent 不读彼此的中间推理, 只通过 evidences 这块"黑板"交换 —— 对齐 SSOT §6
    "不让多个 LLM 无约束互相聊天"。
"""

import operator
from typing import Annotated, Any, Dict, List, TypedDict

from app.runtime.transitions import StateTransition


class DeepDiagnosisState(TypedDict, total=False):
    """群聊深度诊断图的共享状态。"""

    # —— 沿用 fast 的字段 ——
    input: str
    diagnosis_mode: str
    requested_diagnosis_mode: str
    alert_signature: str
    transition_history: Annotated[List[StateTransition], operator.add]

    # —— 诊断对象上下文 (IncidentManager 填) ——
    incident_group_id: str
    incident_id: str
    task_id: str

    # —— ③ EvidencePlan: 派哪几个专业 subagent + 取证策略 ——
    evidence_plan: Dict[str, Any]

    # —— ④ 并行专业 subagent 往这里累加 (operator.add = 并发安全归并) ——
    #    每条 evidence 与 app/evidence/models.EvidenceCreate 对齐:
    #    {source, type, summary, content, score?, metadata?}
    evidences: Annotated[List[Dict[str, Any]], operator.add]

    # —— ④' EvidenceReducer + C(知识图谱) 的 RootCauseLocalizer 产物 ——
    #    [{candidate, paths, support_score, evidence_ids}]
    candidates: List[Dict[str, Any]]

    # —— ⑤ RCAJudge ——
    rca: Dict[str, Any]
    # —— ⑥ RemediationPlanner (写操作必须 requires_human_confirm=True) ——
    remediation: Dict[str, Any]
    # —— ⑦ ReportAgent: 填 response 即触发 END ——
    response: str
