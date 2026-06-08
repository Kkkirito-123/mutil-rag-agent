"""LangGraph State 定义.

Plan-Execute 模式下, 状态在三个节点 (Planner/Executor/Replanner) 之间流转.
状态字段必须满足 LangGraph 的 reducer 约定:
  - 普通字段: 默认行为 = 覆盖 (新值替换旧值)
  - Annotated[List, operator.add]: 累加 (新值追加到旧值后面)

这个文件定义了:
  - PlanExecuteState (TypedDict)        : 整个图的状态
  - Plan, Response, Act (Pydantic)     : Planner/Replanner 的结构化输出
"""

import operator
from typing import Annotated, List, Tuple, TypedDict

from pydantic import BaseModel, Field
from typing_extensions import TypedDict as TE_TypedDict

from app.runtime.transitions import StateTransition


# ============================================================
# tried_skills 单条记录结构 (借鉴 NeurIPS 2025 "failure memory" 思路)
# 不只记 skill 名，还记 "为什么这个方向不对"，下次 LLM 决策时避免重复选回
# ============================================================
class TriedSkill(TE_TypedDict, total=False):
    skill: str          # 已尝试过的 skill name
    reason: str         # 为什么被认为不合适 (供下次 Replanner 参考)


# ============================================================
# 状态定义 (TypedDict, LangGraph 标准模式)
# ============================================================
class PlanExecuteState(TypedDict, total=False):
    """Plan-Execute 多智能体的共享状态.

    字段说明:
        input:           用户原始问题/告警 (不变)
        diagnosis_mode:  实际执行模式, 本期 fast=日常 plan-execute-replan
        requested_diagnosis_mode: 前端/队列请求的模式, deep 先作为多 Agent 组诊断入口预留
        selected_skill:  Skill Router 选中的 skill name (snake_case)
        skill_reason:    Router 选择该 Skill 的一句话理由 (可观测/调试用)
        alert_signature: 同类问题指纹 (app/reflection/signature.py)。由持有结构化
                         payload 的 runner 算好透传, 供 skill_router 召回历史经验回灌。
                         手动诊断无结构化告警时为空, skill_router 退化用 input 近似。
        plan:            待执行的步骤列表 (Replanner 会更新)
        past_steps:      已执行的 (步骤, 结果) 元组列表 (用 operator.add 累加)
        response:        最终响应 (Replanner 决定终止时填充, 触发 END)
        iteration:       当前已执行的步骤数 (硬性防死循环)
        permission_mode: §1 cc-haha 借鉴, 当前会话的工具权限模式 (read_only / normal /
                         ask_destructive / bypass), 默认从 settings.permission_mode 取
        transition_history: §6 cc-haha 借鉴, 每个节点出口的 transition 记录 (结构化时间线).
                            用 operator.add 累加, 节点返回单条 list 即可追加.
    """

    input: str
    diagnosis_mode: str
    requested_diagnosis_mode: str
    alert_signature: str
    selected_skill: str
    skill_reason: str
    plan: List[str]
    past_steps: Annotated[List[Tuple[str, str]], operator.add]
    response: str
    iteration: int
    permission_mode: str
    transition_history: Annotated[List[StateTransition], operator.add]
    # ===== Skill reroute (Supervisor + Handoff 保守版) =====
    # 参考: LangGraph Supervisor + Handoff + NeurIPS 2025 failure memory
    reroute_count: int                                     # 已触发的 reroute 次数
    tried_skills: Annotated[List[TriedSkill], operator.add]  # 已试过的 skill + 被拒原因
    pending_reroute: bool                                  # 临时标记: replanner 本轮决定 reroute, 带回 Planner


# ============================================================
# Planner 的结构化输出
# ============================================================
class Plan(BaseModel):
    """诊断计划: 一组待执行的步骤."""

    steps: List[str] = Field(
        ...,
        description=(
            "按顺序执行的步骤列表, 4-6 步为宜. "
            "每步必须可以通过工具调用 (查日志/查指标/查知识库) 完成, "
            "或基于已有信息直接推理。"
        ),
    )


# ============================================================
# Replanner 的结构化输出
# ============================================================
# 设计说明:
#   原 Plan-Execute 教程使用 Union[Response, Plan], 但通义千问对 Union 类型
#   兼容不佳 (会返回字符串 'Plan' 而非对象). 改用单一 schema + bool discriminator.
class Act(BaseModel):
    """Replanner 的决策结果.

    is_finished 是核心 discriminator:
      - True  → 流程结束, 取 response 字段作为最终报告
      - False → 流程继续, 取 plan 字段作为剩余步骤
    """

    is_finished: bool = Field(
        ...,
        description=(
            "诊断流程是否完成. "
            "true = 已收集到足够信息, 可以生成最终报告; "
            "false = 还需继续执行剩余步骤"
        ),
    )
    plan: List[str] = Field(
        default_factory=list,
        description=(
            "剩余要执行的步骤列表 (仅当 is_finished=false 时有值). "
            "不要包含已经完成过的步骤."
        ),
    )
    response: str = Field(
        default="",
        description=(
            "完整的诊断报告 Markdown (仅当 is_finished=true 时有值). "
            "包含问题概述、根因分析、关键证据、处置建议、结论"
        ),
    )
    # ===== Skill reroute (Supervisor + Handoff) =====
    # LLM 只负责"提议"是否切 Skill, 最终是否生效由 replanner.py 代码校验
    # (检查 reroute 次数上限 / tried_skills 黑名单 / past_steps 门槛 / skill 是否存在)
    should_reroute: bool = Field(
        default=False,
        description=(
            "是否建议切换 Skill 重新规划. "
            "仅在以下情况设 true: "
            "(1) 当前 Skill 的关键证据明确不成立 (例: host_resource_diagnosis 但 CPU/内存/磁盘全部正常); "
            "(2) 工具结果明显指向另一个故障域 (例: 查 CPU 时发现 Redis 内存 98%); "
            "(3) 当前 Skill 的关键工具全部不可用. "
            "其他情况一律走 is_finished 或继续 replan, 不要设 true."
        ),
    )
    new_skill: str = Field(
        default="",
        description=(
            "要切换到的新 Skill name (snake_case). "
            "仅当 should_reroute=true 时有值. "
            "必须是候选 Skill 菜单中的名字, 且不在 tried_skills 黑名单里."
        ),
    )
    reroute_reason: str = Field(
        default="",
        description=(
            "切换 Skill 的具体证据和原因 (一句话). "
            "仅当 should_reroute=true 时有值. "
            "会被写入 tried_skills 供后续决策参考."
        ),
    )
