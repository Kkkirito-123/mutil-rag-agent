"""Skill 工具过滤 + Permission 决策.

职责: 在 Executor 调用 LLM 前, 把全量工具收窄成"当前 Skill 在当前 Mode 下能用的工具",
并产出每个工具的 PermissionDecision (allow/ask/deny + reason_type) 给 tool_runner 使用.

设计原则 (§1 cc-haha 借鉴):
  - 三层防御: Skill allowlist (硬墙) → Mode 限制 → Guardrails 黑名单
  - 决策可解释: 每个工具都生成 PermissionDecision, 失败时带 reason_type
  - 暴露策略: allow + ask 工具都给 LLM 看到 (ask 在运行时再走审批);
              deny 工具直接不给 LLM 看, LLM 想都想不到去调
"""

from typing import Dict, List, Literal, Optional, Tuple

from langchain_core.tools import BaseTool
from loguru import logger

from app.config import settings
from app.runtime.permissions import (
    PermissionDecision,
    PermissionMode,
    evaluate_permission,
)
from app.skills.registry import get_skill_registry
from app.tools.lazy_mcp_tools import expose_tools_with_lazy_mcp
from app.tools.meta import TOOL_META, get_meta

ToolRisk = Literal["low", "medium", "high"]


# ============================================================
# 高危 / 通知工具集合 (派生自 TOOL_META, 给 evaluate_permission 用)
# ============================================================
# 高危 = risk_level == "high" 或 destructive == True
# 通知 = is_notification == True
HIGH_RISK_TOOLS: set[str] = {
    name
    for name, meta in TOOL_META.items()
    if meta.risk_level == "high" or meta.destructive
}

NOTIFICATION_TOOLS: set[str] = {
    name
    for name, meta in TOOL_META.items()
    if meta.is_notification
}


def _tool_risk(tool_name: str) -> ToolRisk:
    return get_meta(tool_name).risk_level


# ============================================================
# 旧版静态 Guardrails 检查 (向后兼容)
# 新代码请用 evaluate_permission()
# ============================================================
def _is_tool_allowed_by_guardrails(tool_name: str) -> bool:
    """[已替代] 仅静态检查高危/通知黑名单, 不考虑 Mode.

    替代品: app.runtime.permissions.evaluate_permission()
    保留原因: smoke_tool_meta.py 的 backward-compat 测试.
    """
    if settings.guardrails_block_high_risk_tools and tool_name in HIGH_RISK_TOOLS:
        return False
    if not settings.guardrails_allow_notification_tools and tool_name in NOTIFICATION_TOOLS:
        return False
    return True


# ============================================================
# 主入口: 给 Executor 用
# ============================================================
def filter_tools_for_skill(
    selected_skill_name: Optional[str],
    tools: List[BaseTool],
    *,
    mode: PermissionMode = PermissionMode.NORMAL,
) -> Tuple[List[BaseTool], Dict[str, PermissionDecision]]:
    """按 Skill + PermissionMode 过滤工具集, 同时返回每个工具的权限决策.

    返回值是元组 (visible_tools, decisions):
      - visible_tools: 给 LLM bind_tools 用 (allow + ask 都暴露, deny 不给看)
      - decisions:     运行时 tool_runner 用 (ask -> 走审批, allow -> 直接调)

    Args:
        selected_skill_name: SkillRouter 选定的 skill (None -> generic_oncall 兜底)
        tools: get_all_tools() 给的全量工具列表
        mode: 权限模式 (read_only / normal / ask_destructive / bypass)

    Returns:
        (visible_tools, decisions_for_all_skill_tools)
    """
    registry = get_skill_registry()
    skill = registry.get_or_generic(selected_skill_name)
    allowed = set(skill.allowed_tools)

    if not allowed:
        logger.warning(
            f"[Harness] Skill {skill.name} 未配置 allowed_tools, 拒绝暴露工具给 Executor"
        )
        return [], {}

    # ---- Step 1: 组装 Skill 可见工具集 ----
    # 策略 (2026-05-02): 除 Skill allowed_tools 外, 把所有 "只读工具" 也纳入候选,
    # 目的是避免 Skill 漏配某个查询工具导致诊断时无法获取真实数据.
    # 写/通知/高危工具仍然必须显式列在 allowed_tools 里才能出现.
    available_names = {tool.name for tool in tools}
    skill_tools: List[BaseTool] = []
    auto_readonly_added: list[str] = []
    seen_names: set[str] = set()
    for tool in tools:
        if tool.name in seen_names:
            continue
        if tool.name in allowed:
            skill_tools.append(tool)
            seen_names.add(tool.name)
            continue
        # Skill 未显式声明, 但是只读工具 → 自动放入候选
        if get_meta(tool.name).read_only:
            skill_tools.append(tool)
            seen_names.add(tool.name)
            auto_readonly_added.append(tool.name)

    decisions: Dict[str, PermissionDecision] = {}
    for tool in skill_tools:
        decisions[tool.name] = evaluate_permission(
            tool.name,
            tool_input=None,
            skill_allowed=allowed,
            mode=mode,
            block_high_risk=settings.guardrails_block_high_risk_tools,
            allow_notification=settings.guardrails_allow_notification_tools,
        )

    # ---- Step 2: allow + ask 暴露给 LLM, deny 不暴露 ----
    visible_tools = [t for t in skill_tools if decisions[t.name].behavior in ("allow", "ask")]
    deny_names = sorted(t.name for t in skill_tools if decisions[t.name].behavior == "deny")
    ask_names = sorted(t.name for t in skill_tools if decisions[t.name].behavior == "ask")

    # ---- Step 3: Lazy MCP 替换 (把直接 MCP 工具替换成两个元工具) ----
    visible_tools = expose_tools_with_lazy_mcp(
        visible_tools,
        {t.name for t in visible_tools},
        enabled=settings.mcp_lazy_tools_enabled,
    )

    # ---- Step 4: 结构化日志 (排错友好, reason_type 直接 grep) ----
    missing = sorted(allowed - available_names)
    skill_filtered_out = sorted(t.name for t in tools if t.name not in allowed)
    enabled_risks = {tool.name: _tool_risk(tool.name) for tool in visible_tools}

    logger.info(
        f"[Harness] Skill={skill.name} mode={mode.value} risk={skill.risk_level} "
        f"visible={[t.name for t in visible_tools]} "
        f"deny={deny_names} ask={ask_names} "
        f"skill_filtered={skill_filtered_out} "
        f"auto_readonly={auto_readonly_added} "
        f"enabled_risks={enabled_risks} mcp_lazy={settings.mcp_lazy_tools_enabled}"
    )
    if missing:
        logger.warning(f"[Harness] Skill={skill.name} 配置了未加载工具: {missing}")
    for name in deny_names:
        d = decisions[name]
        logger.info(f"[Harness] deny tool={name} reason_type={d.reason_type} reason={d.reason}")
    for name in ask_names:
        d = decisions[name]
        logger.info(f"[Harness] ask  tool={name} reason_type={d.reason_type} reason={d.reason}")

    return visible_tools, decisions
