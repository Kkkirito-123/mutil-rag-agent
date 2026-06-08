"""LangGraph 图编排.

图结构 (Skill Router + Plan-Execute-Replan):

    [START]
       │
       ▼
   ┌──────────────┐
   │ SkillRouter  │  (在 Skill 列表中选一个, 写 state.selected_skill)
   └──────┬───────┘
          │
     ┌────┴────┐
     │ Router  │
     │已 response?│── yes ──► [END]
     └────┬────┘
         no
          ▼
   ┌──────────┐
   │ Planner  │  (基于选定 Skill 的 Playbook, 制定 4-6 步计划)
   └─────┬────┘
         ▼
   ┌──────────┐
   │ Executor │  (执行 plan[0], 调用工具)
   └─────┬────┘
         ▼
   ┌──────────┐
   │Replanner │  (评估进度)
   └─────┬────┘
         │
    ┌────┴────┐
    │ should  │
    │  end?   │   ── yes ──► [END]
    └────┬────┘
        no
         ▼
       (loop back to Executor)

设计要点:
  - 起点是 SkillRouter, 跑一次, 然后交给 Planner
  - Executor 和 Replanner 之间通过 conditional edge 形成循环
  - should_end() 通过检查 state["response"] 是否非空来决定终止
"""

from typing import Literal

from langgraph.graph import END, START, StateGraph
from loguru import logger

from app.agents.executor import execute_node
from app.agents.planner import plan_node
from app.agents.replanner import replan_node
from app.agents.skill_router import skill_router_node
from app.agents.state import PlanExecuteState


def should_end(state: PlanExecuteState) -> Literal["executor", "planner", "__end__"]:
    """Replanner 后的条件边: 三向路由.

    优先级:
      1. 已生成 response → END
      2. pending_reroute=True → 回 planner 重新规划 (Supervisor + Handoff 保守版)
      3. plan 为空 + 无 response → 强制 END (防死循环)
      4. 默认 → 回 executor 继续跳下一步
    """
    response = state.get("response", "")
    if response:
        logger.info("[Graph] 收到 response, 流程结束")
        return END
    if state.get("pending_reroute"):
        logger.info(
            f"[Graph] 检测到 pending_reroute, 路由回 Planner 重新规划 "
            f"(new selected_skill={state.get('selected_skill', '?')})"
        )
        return "planner"
    if not state.get("plan"):
        logger.warning("[Graph] plan 为空且无 response, 强制终止")
        return END
    return "executor"


def route_after_skill(state: PlanExecuteState) -> Literal["planner", "__end__"]:
    """skill_router 之后的路由.

    优先级:
      1. Router 已生成 response (非 OnCall 输入 / 兜底场景) → END
      2. 默认 → planner
    """
    response = state.get("response", "")
    if response:
        logger.info("[Graph] Router 已生成 response, 跳过 Planner/Executor")
        return END
    return "planner"


def build_aiops_graph():
    """构建 AIOps 多智能体 graph.

    Returns:
        编译后的 CompiledStateGraph, 可以 .ainvoke() / .astream() 调用
    """
    workflow = StateGraph(PlanExecuteState)

    # 节点
    workflow.add_node("skill_router", skill_router_node)
    workflow.add_node("planner", plan_node)
    workflow.add_node("executor", execute_node)
    workflow.add_node("replanner", replan_node)

    # 边
    workflow.add_edge(START, "skill_router")
    workflow.add_conditional_edges(
        "skill_router",
        route_after_skill,
        {
            "planner": "planner",
            END: END,
        },
    )
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "replanner")

    # 条件边: replanner -> executor (继续) / planner (Skill reroute) / END (终止)
    workflow.add_conditional_edges(
        "replanner",
        should_end,
        {
            "executor": "executor",
            "planner": "planner",
            END: END,
        },
    )

    compiled = workflow.compile()
    logger.info("[Graph] AIOps graph 已编译完成 (skill_router + plan-execute-replan)")
    return compiled
