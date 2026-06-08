"""Executor 节点: 执行 plan[0], 用工具收集信息.

设计要点:
  - 默认走 app.agents.parallel_agent.run_parallel_agent (§3 cc-haha 借鉴):
    单步内 read-only 工具按 ToolMeta.concurrency_safe 切批 asyncio.gather 并行,
    遇到写工具自动切批走串行, 顺序仍然受保护.
  - 通过 settings.executor_parallel_enabled=False 可回退到 langchain.agents.create_agent
    (默认串行) 用于排错对比.
  - 工具来自 mcp_loader.get_all_tools(), 经 Harness (filter_tools_for_skill) 过滤.
  - 每次执行后, 把 (step, result) 追加到 past_steps.
"""

from typing import Any, Dict, List, Tuple

from langchain.agents import create_agent
from langchain_core.tools import BaseTool
from loguru import logger

from app.runtime.permissions import (
    PermissionDecision,
    PermissionMode,
    parse_permission_mode,
)
from app.runtime.agent_harness import get_agent_harness
from app.runtime.tool_filter import filter_tools_for_skill
from app.runtime.tool_runner import run_parallel_agent
from app.runtime.transitions import (
    EXECUTOR_MAX_STEPS,
    EXECUTOR_OK,
    EXECUTOR_TOOL_ERROR,
    make_transition,
)
from app.agents.state import PlanExecuteState
from app.runtime.stream_sink import emit as emit_stream, set_step
from app.config import settings
from app.core.llm import get_chat_llm
from app.tools.mcp_loader import get_all_tools

# 缓存 (skill, tool_names, runner_mode, perm_mode) → (tools, decisions, executor)
# - 并行模式下 executor 是 (llm, tools) 二元组, run_parallel_agent 是无状态函数
# - 串行 fallback 模式下 executor 是 create_agent 返回的 Runnable
# - cache_key 加 perm_mode, 切换 PermissionMode 会自动重建 (decisions 不同)
_agent_cache: Dict[Tuple[str, Tuple[str, ...], str, str], Any] = {}


def _get_executor(
    selected_skill_name: str,
    perm_mode: PermissionMode,
) -> Tuple[str, Any, List[BaseTool], Dict[str, PermissionDecision]]:
    """返回 (runner_mode, executor, tools, decisions).

    runner_mode 取值:
      - "parallel"  → executor 是 (llm, tools) 二元组, 调用方走 run_parallel_agent
      - "serial"    → executor 是 create_agent 返回的 Runnable, 调用方走 .ainvoke

    Skill / 工具列表 / runner mode / PermissionMode 变化时会自动重建.
    """
    tools, decisions = filter_tools_for_skill(
        selected_skill_name, get_all_tools(), mode=perm_mode
    )
    tool_names = tuple(t.name for t in tools)
    harness = get_agent_harness()
    runner_mode = "parallel" if harness.executor_parallel_enabled() else "serial"
    cache_key = (selected_skill_name or "", tool_names, runner_mode, perm_mode.value)

    if cache_key not in _agent_cache:
        logger.info(
            f"[Executor] 创建 Agent: skill={selected_skill_name or '(none)'} "
            f"runner={runner_mode} perm={perm_mode.value} tools={list(tool_names)}"
        )
        # Executor 跑得最频繁 (每步一次 LLM, 多步累计 5-10 次), 是延迟瓶颈.
        # 默认走 agent_executor_model (推荐配 flash); 留空则回退 dashscope_chat_model.
        executor_model = harness.executor_model()
        if runner_mode == "parallel":
            # streaming=True 很关键:
            #   1. 前端 mon-stream 才能看到打字机效果 (否则 astream 退化成一次性大 chunk)
            #   2. get_chat_llm 会自动加 stream_usage=True → stream_options.include_usage,
            #      最后一帧才带真实 usage_metadata, 监控卡片才能从"~估算"变"API 实测"
            llm = get_chat_llm(model=executor_model, temperature=0, streaming=True)
            _agent_cache[cache_key] = (llm, tools)
        else:
            _agent_cache[cache_key] = create_agent(
                model=get_chat_llm(model=executor_model, temperature=0, streaming=True),
                tools=tools,
                system_prompt=harness.executor_system_prompt(),
            )

    return runner_mode, _agent_cache[cache_key], tools, decisions


async def execute_node(state: PlanExecuteState) -> PlanExecuteState:
    """Executor 节点: 执行 plan[0], 把结果加到 past_steps."""
    plan = state.get("plan", [])
    if not plan:
        logger.warning("[Executor] 计划为空, 跳过")
        return {}

    current_step = plan[0]
    iteration = state.get("iteration", 0) + 1
    total_steps = len(plan)

    logger.info(f"[Executor] 第 {iteration} 步执行: {current_step}")
    # 把当前步号放进 context, 让 tool_runner 的 emit() 自动带 iteration.
    # 同时推一条 step_start, 让前端能在 LLM token 到来前就先占好卡片.
    set_step(iteration)
    await emit_stream({
        "type": "step_start",
        "iteration": iteration,
        "step": current_step,
        "total": total_steps,
    })

    # 防死循环: 硬性步数上限
    harness = get_agent_harness()
    if iteration > harness.max_agent_steps():
        logger.warning(
            f"[Executor] 已达最大步数 {harness.max_agent_steps()}, 强制返回兜底结果"
        )
        logger.warning(f"[transition] node=executor reason={EXECUTOR_MAX_STEPS} detail=iteration={iteration}")
        return {
            "past_steps": [(current_step, "[超过最大步数, 强制中止本步]")],
            "iteration": iteration,
            "transition_history": [
                make_transition("executor", EXECUTOR_MAX_STEPS, f"iteration={iteration}"),
            ],
        }

    selected_skill_name = state.get("selected_skill", "")
    perm_mode = parse_permission_mode(
        state.get("permission_mode") or harness.default_permission_mode()
    )
    runner_mode, executor, tools, decisions = _get_executor(selected_skill_name, perm_mode)

    task_prompt = harness.build_executor_task_prompt(
        plan=plan,
        step_index=iteration,
        total_steps=total_steps,
        current_step=current_step,
    )

    transition_reason = EXECUTOR_OK
    transition_detail = f"iter={iteration}/{total_steps}"
    try:
        if runner_mode == "parallel":
            llm, parallel_tools = executor
            policy = harness.executor_policy()
            result = await run_parallel_agent(
                llm=llm,
                tools=parallel_tools,
                system_prompt=harness.executor_system_prompt(),
                inputs={"messages": [("user", task_prompt)]},
                max_iters=policy.max_iters,
                max_parallel=policy.max_parallel,
                decisions=decisions,
            )
        else:
            # 串行 fallback (create_agent) 不支持 decisions, 只依赖 Harness 预过滤
            result = await executor.ainvoke({"messages": [("user", task_prompt)]})
        # 两条路径都返回 {"messages": [...]}, 取最后一条 AI 消息内容
        last_msg = result["messages"][-1]
        answer = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    except Exception as e:
        logger.exception(f"[Executor] 工具调用失败: {e}")
        answer = f"[执行失败: {type(e).__name__}: {e}]"
        transition_reason = EXECUTOR_TOOL_ERROR
        transition_detail = f"{type(e).__name__}: {e}"
        logger.warning(f"[transition] node=executor reason={transition_reason} detail={transition_detail}")

    preview = answer[:100].replace("\n", " ")
    logger.info(f"[Executor] 完成: {preview}...")

    return {
        "past_steps": [(current_step, answer)],
        "iteration": iteration,
        "transition_history": [
            make_transition("executor", transition_reason, transition_detail),
        ],
    }
