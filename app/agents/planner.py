"""Planner 节点: 把用户问题拆解为多步诊断计划.

设计要点:
  - 使用 with_structured_output(Plan) 强制 LLM 返回 Pydantic 对象
    → 不用解析 JSON 字符串, 不会因为 LLM 格式错误而 crash
  - temperature=0 保证拆分稳定 (相同输入 → 相同步骤)
  - **基于 Skill 的 Playbook 拆**: 从 state.selected_skill 取出 Skill, 把 playbook
    作为种子注入 user prompt, 让 LLM 在 Playbook 基础上生成具体步骤
  - 兜底: 如果 LLM 返回空步骤, 给一个 fallback 计划 (避免下游 executor 卡死)
"""

from loguru import logger

from app.agents.state import Plan, PlanExecuteState
from app.core.llm import get_chat_llm
from app.core.structured import ainvoke_structured
from app.runtime.agent_harness import get_agent_harness
from app.runtime.transitions import (
    PLANNER_EMPTY_STEPS,
    PLANNER_LLM_FAILED,
    PLANNER_OK,
    make_transition,
)
from app.skills import get_skill_registry


async def plan_node(state: PlanExecuteState) -> PlanExecuteState:
    """Planner 节点: 输入 state.input + state.selected_skill, 输出 state.plan."""
    user_input = state["input"]
    skill_name = state.get("selected_skill", "")

    # 取选定 Skill, 找不到时回退到 generic_oncall (registry 保证 fallback 存在)
    registry = get_skill_registry()
    skill = registry.get_or_generic(skill_name)

    is_reroute = state.get("pending_reroute", False)
    if is_reroute:
        logger.info(
            f"[Planner] reroute 后重新规划 (skill={skill.name}): {user_input[:100]}..."
        )
    else:
        logger.info(
            f"[Planner] 开始拆分任务 (skill={skill.name}): {user_input[:100]}..."
        )

    harness = get_agent_harness()
    planner_model = harness.planner_model()
    llm = get_chat_llm(model=planner_model, temperature=0, timeout=30, max_retries=1)

    messages = harness.build_planner_messages(
        user_input=user_input,
        skill_display_name=skill.display_name,
        skill_playbook=skill.playbook,
    )

    try:
        plan = await ainvoke_structured(
            llm=llm,
            schema_cls=Plan,
            messages=messages,
            model_name=planner_model,
        )
    except Exception as e:
        detail = f"{type(e).__name__}: {e}"
        logger.exception(f"[Planner] 结构化输出失败, 使用 fallback 计划: {e}")
        logger.warning(f"[transition] node=planner reason={PLANNER_LLM_FAILED} detail={detail}")
        return {
            "plan": harness.planner_fallback_plan("llm_failed"),
            "iteration": 0,
            "pending_reroute": False,  # 清标记, 避免下轮误路由
            "transition_history": [make_transition("planner", PLANNER_LLM_FAILED, detail)],
        }

    if not plan.steps:
        logger.warning("[Planner] LLM 返回空 steps, 使用 fallback")
        logger.warning(f"[transition] node=planner reason={PLANNER_EMPTY_STEPS}")
        return {
            "plan": harness.planner_fallback_plan("empty_plan"),
            "iteration": 0,
            "pending_reroute": False,
            "transition_history": [make_transition("planner", PLANNER_EMPTY_STEPS, "LLM 返回空 steps")],
        }

    logger.info(f"[Planner] 已生成 {len(plan.steps)} 步计划 (skill={skill.name}):")
    for i, step in enumerate(plan.steps, 1):
        logger.info(f"  Step {i}: {step}")

    return {
        "plan": plan.steps,
        "iteration": 0,
        "pending_reroute": False,  # 清标记, 避免下轮误路由
        "transition_history": [
            make_transition(
                "planner",
                PLANNER_OK,
                f"skill={skill.name} steps={len(plan.steps)}"
                + (" (reroute)" if is_reroute else ""),
            ),
        ],
    }
