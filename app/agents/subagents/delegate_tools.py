"""§5 Subagent runner: 把每个 SubagentDefinition 包装成主 Executor 可见的 BaseTool.

主 Executor 通过 ainvoke({"name": "delegate_to_evidence_collector",
                          "args": {"task": "..."}}) 来委托.

设计要点:
  - 每个 delegate_to_<agent_type> 工具内部独立跑一个 ReAct 循环 (复用 §3 run_parallel_agent)
  - Subagent 自己的工具池由 SubagentDefinition.allowed_tools 控制 (绝对硬墙, 不暴露其他)
  - 内部走 §1 PermissionMode "ALLOW" 决策 (因为已经经过 SubagentDefinition 白名单一次过滤)
  - 内部不再嵌套 delegate_to_* (在 allowed_tools 里就没放, 自然套不起来)
  - 异常被吃掉返回错误字符串, 不让 subagent 异常击穿主 Executor
"""

from __future__ import annotations

from typing import Dict, List, Optional

from langchain_core.tools import BaseTool, StructuredTool
from loguru import logger
from pydantic import BaseModel, Field

from app.agents.subagents.registry import SUBAGENTS, SubagentDefinition
from app.core.llm import get_chat_llm
from app.runtime.permissions import PermissionDecision
from app.runtime.tool_runner import run_parallel_agent


class _DelegateInput(BaseModel):
    """所有 delegate_to_* 工具的统一输入 schema."""

    task: str = Field(
        ...,
        description=(
            "委托给二级 Agent 的具体任务描述. 用自然语言, 给清楚: "
            "做什么 + 上下文 + 需要的输出形态."
        ),
    )


def _resolve_subagent_tools(sub: SubagentDefinition, all_tools: List[BaseTool]) -> List[BaseTool]:
    """从 all_tools 中按 sub.allowed_tools 过滤 subagent 实际能用的工具."""
    available = {t.name: t for t in all_tools}
    return [available[name] for name in sub.allowed_tools if name in available]


async def _run_subagent(sub: SubagentDefinition, task: str) -> str:
    """执行一次 subagent 委托, 返回 final answer 字符串.

    流程:
      1. 从 get_all_tools() 拉全集, 按 sub.allowed_tools 过滤出 subagent 工具池
      2. 给每个工具一个 allow 决策 (subagent 内部不再做权限检查, 信任白名单)
      3. 调 run_parallel_agent, 拿最后一条 AIMessage.content
    """
    # 延迟 import 避免循环 (subagents.delegate_tools -> tools -> subagents)
    from app.tools.mcp_loader import get_all_tools as _get_all_tools

    all_tools = _get_all_tools()
    sub_tools = _resolve_subagent_tools(sub, all_tools)

    if sub.allowed_tools and not sub_tools:
        msg = (
            f"[{sub.agent_type}] 配置的 allowed_tools 在当前运行环境一个都没找到. "
            f"期望: {sub.allowed_tools}. 检查 MCP server 是否启动."
        )
        logger.warning(msg)
        return msg

    decisions: Dict[str, PermissionDecision] = {
        t.name: PermissionDecision(behavior="allow", reason_type="ok")
        for t in sub_tools
    }

    logger.info(
        f"[Subagent] type={sub.agent_type} 开始执行: tools={[t.name for t in sub_tools]} "
        f"max_iters={sub.max_iters} task_preview={task[:80]!r}"
    )

    try:
        if not sub_tools:
            # report_writer 没工具, run_parallel_agent 要求 tools 非空
            # 直接调 LLM 跑一轮
            llm = get_chat_llm(temperature=0.2)
            ai_msg = await llm.ainvoke(
                [
                    {"role": "system", "content": sub.system_prompt},
                    {"role": "user", "content": task},
                ]
            )
            content = ai_msg.content if hasattr(ai_msg, "content") else str(ai_msg)
        else:
            result = await run_parallel_agent(
                llm=get_chat_llm(temperature=0),
                tools=sub_tools,
                system_prompt=sub.system_prompt,
                inputs={"messages": [("user", task)]},
                max_iters=sub.max_iters,
                decisions=decisions,
            )
            last = result["messages"][-1]
            content = last.content if hasattr(last, "content") else str(last)
    except Exception as exc:
        logger.exception(f"[Subagent] type={sub.agent_type} 执行异常: {exc}")
        return f"[{sub.agent_type} 执行失败: {type(exc).__name__}: {exc}]"

    if not isinstance(content, str):
        content = str(content)

    # 截断保护
    if len(content) > sub.max_result_chars:
        original = len(content)
        content = (
            content[: sub.max_result_chars]
            + f"\n[truncated: original {original} chars, kept first {sub.max_result_chars}]"
        )

    logger.info(
        f"[Subagent] type={sub.agent_type} 完成: result_len={len(content)}"
    )
    return content


def _make_delegate_tool(sub: SubagentDefinition) -> BaseTool:
    """把一个 SubagentDefinition 包装成 StructuredTool."""

    async def _coroutine(task: str) -> str:
        return await _run_subagent(sub, task)

    return StructuredTool.from_function(
        coroutine=_coroutine,
        name=f"delegate_to_{sub.agent_type}",
        description=sub.description,
        args_schema=_DelegateInput,
    )


# 模块级缓存: subagent tool 不变, 不需要每次 get_all_tools() 都新建
_subagent_tools_cache: Optional[List[BaseTool]] = None


def get_subagent_tools() -> List[BaseTool]:
    """返回所有 delegate_to_* 工具.

    主 Executor 通过 get_all_tools() 间接拿到这些工具, Skill 在 allowed_tools 里
    引用 delegate_to_<agent_type> 即可委托.
    """
    global _subagent_tools_cache
    if _subagent_tools_cache is None:
        _subagent_tools_cache = [_make_delegate_tool(sub) for sub in SUBAGENTS.values()]
        logger.info(
            f"[Subagent] 已注册 {len(_subagent_tools_cache)} 个 delegate 工具: "
            f"{[t.name for t in _subagent_tools_cache]}"
        )
    return list(_subagent_tools_cache)
