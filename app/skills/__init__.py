"""Skill 层: OnCall Agent 的故障处理剧本 (Playbook) 抽象.

设计目标:
  - 把"怎么排障"从 Prompt 中解耦, 沉淀为可复用、可版本管理的 SKILL.md
  - Planner 不再用一份通用 Prompt 拆所有故障, 而是基于 Skill 的 Playbook 拆
  - Executor 工具白名单由 runtime.tool_filter 强制收窄

关键概念:
  - Skill        : 面向某类故障的剧本 (例如 host_resource_diagnosis / network_diagnosis)
  - SkillRegistry: 启动时加载内置 definitions/ 与可选外部目录中的 SKILL.md, 单例

模块对外接口:
  - get_skill_registry()  : 全局单例
  - reload_skill_registry(): 清缓存并重新扫描
  - Skill, SkillRegistry  : 类型
"""

from app.skills.models import Skill
from app.skills.registry import (
    GENERIC_SKILL_NAME,
    SkillRegistry,
    get_skill_registry,
    reload_skill_registry,
)

__all__ = [
    "Skill",
    "SkillRegistry",
    "GENERIC_SKILL_NAME",
    "get_skill_registry",
    "reload_skill_registry",
]
