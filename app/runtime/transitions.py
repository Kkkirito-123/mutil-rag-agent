"""§6 cc-haha 借鉴: 状态转换原因枚举 (Transition Reasons).

每个 LangGraph 节点的"正常出口 + 异常兜底"都用这里的常量打日志 + 写 state.transition_history.
日志格式 (在节点里手动打): [transition] node=replanner reason=replanner_max_steps_force detail=已达 8 步

设计理念:
  - 把"为什么走到这条出口"从藏在日志正文升级成结构化字段
  - 5-6 条兜底分支不再都进同一个 _force_summary 出口, 排障一眼定位
  - 前端用 transition_history 渲染时间线, 演示可观测性
  - 未来加 cc-haha 那样的真正恢复策略 (collapse/compact/escalate) 只是加常量

参考:
  cc-haha docs/agent/03-agent-framework.md:524-545 transitionReasons 枚举
"""

from __future__ import annotations

from datetime import datetime
from typing import TypedDict


# ============================================================
# Reason 枚举 (按节点分组, 命名一律 <node>_<event>)
# ============================================================

# === Skill Router ===
ROUTER_OUT_OF_SCOPE = "router_out_of_scope"        # 非 OnCall 输入, 直接终止 (response 已填)
ROUTER_LLM_FAILED = "router_llm_failed"            # Router LLM 异常, 走规则兜底
ROUTER_FALLBACK_GENERIC = "router_fallback_generic"  # LLM 返回未知 skill, 回退 generic
ROUTER_OK = "router_ok"                            # 正常选定 skill
ROUTER_RECALL_APPLIED = "router_recall_applied"    # 回灌: 注入同类告警历史经验到路由 prompt

# === Planner ===
PLANNER_LLM_FAILED = "planner_llm_failed"          # 结构化输出失败, 走 fallback plan
PLANNER_EMPTY_STEPS = "planner_empty_steps"        # LLM 返回空 plan, 走 fallback
PLANNER_OK = "planner_ok"                          # 正常生成计划

# === Executor ===
EXECUTOR_MAX_STEPS = "executor_max_steps"          # 达到 agent_max_steps 强制中止本步
EXECUTOR_TOOL_ERROR = "executor_tool_error"        # 工具调用循环抛异常
EXECUTOR_OK = "executor_ok"                        # 正常完成单步

# === Replanner ===
REPLANNER_LLM_FAILED = "replanner_llm_failed"      # structured_output 失败 → _force_summary
REPLANNER_FINISHED_EMPTY = "replanner_finished_empty"  # is_finished=True 但 response 为空
REPLANNER_NOT_FINISHED_EMPTY = "replanner_not_finished_empty"  # is_finished=False 但 plan 空
REPLANNER_MAX_STEPS_FORCE = "replanner_max_steps_force"  # 达到上限强制收尾
REPLANNER_FINISHED_OK = "replanner_finished_ok"    # 正常完成
REPLANNER_CONTINUE = "replanner_continue"          # 正常继续 (返回新 plan)
REPLANNER_REROUTE = "replanner_reroute"            # 触发 Skill reroute (回 Planner 重新规划)
REPLANNER_REROUTE_BLOCKED = "replanner_reroute_blocked"  # LLM 想 reroute 但被规则阻止 (次数/黑名单/证据不足)

# === Permission (留给 §1 在 tool_runner 里发) ===
PERMISSION_DENIED = "permission_denied"
PERMISSION_ASK_TIMEOUT = "permission_ask_timeout"
PERMISSION_ASK_REJECTED = "permission_ask_rejected"

# === Subagent (deep graph 专业 Agent 委派) ===
SUBAGENT_DELEGATED = "subagent_delegated"
SUBAGENT_FAILED = "subagent_failed"

# === Deep Diagnosis (群聊 / M7 多 Agent 组诊断) ===
DEEP_INCIDENT_LOADED = "deep_incident_loaded"          # IncidentManager 载入诊断对象
DEEP_CONTEXT_BUILT = "deep_context_built"              # CorrelationContext 从 KG 拉到上下文
DEEP_EVIDENCE_PLANNED = "deep_evidence_planned"        # EvidencePlan 定下派哪几个专业 subagent
DEEP_AGENT_DONE = "deep_agent_done"                    # 某专业 subagent 产出 Evidence (detail 标明哪个)
DEEP_EVIDENCE_REDUCED = "deep_evidence_reduced"        # EvidenceReducer 归并出候选根因
DEEP_RCA_JUDGED = "deep_rca_judged"                    # RCAJudge 定根因
DEEP_REMEDIATION_PLANNED = "deep_remediation_planned"  # RemediationPlanner 出处置 (待人工确认)
DEEP_REPORT_DONE = "deep_report_done"                  # ReportAgent 出报告
DEEP_STUB = "deep_stub"                                # 节点尚为 stub, 真实逻辑未实现


# ============================================================
# 数据结构
# ============================================================
class StateTransition(TypedDict, total=False):
    """state.transition_history 中的每一条记录.

    字段:
        node:    哪个图节点产出的 (skill_router / planner / executor / replanner)
        reason:  Reason 常量 (上面那些字符串)
        detail:  人话, 一行说明 (排错友好)
        ts:      ISO8601 时间戳, 带时区
    """

    node: str
    reason: str
    detail: str
    ts: str


# ============================================================
# 工厂 (节点里用)
# ============================================================
def make_transition(node: str, reason: str, detail: str = "") -> StateTransition:
    """构造一条 transition 记录. 时间戳自动填充."""
    return {
        "node": node,
        "reason": reason,
        "detail": detail,
        "ts": datetime.now().astimezone().isoformat(timespec="milliseconds"),
    }
