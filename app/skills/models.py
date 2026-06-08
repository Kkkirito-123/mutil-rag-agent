"""Skill 数据模型.

每个 Skill 由一个 SKILL.md 文件描述, 格式为 YAML frontmatter + Markdown body:

    ---
    name: host_resource_diagnosis
    display_name: 主机资源诊断 (CPU/内存/磁盘)
    description: 主机/容器 CPU 高、内存高/OOM、磁盘满、本机卡顿等资源类故障
    triggers: [cpu 高, 内存高, 磁盘满, 我电脑, oom]
    allowed_tools: [search_knowledge_base, get_local_cpu_memory, get_local_disk_usage, list_top_processes]
    risk_level: low
    ---

    # CPU 高使用率排查
    ## 适用场景
    ...
    ## 推荐排查步骤
    1. ...
    ## 输出格式
    ...

frontmatter 字段约束见 Skill 模型, body 原样保留到 Skill.playbook.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

# 风险等级:
#   low    = 仅读操作 (查日志/查指标/查知识库)
#   medium = 调用外部 API, 但不写状态
#   high   = 涉及写操作 (重启服务/删文件/改配置), 必须经 Harness 人工确认
RiskLevel = Literal["low", "medium", "high"]


class Skill(BaseModel):
    """单个 Skill 的运行时表示.

    实例由 loader.load_skill_from_file 从 SKILL.md 解析得到.
    """

    # ===== frontmatter 字段 =====
    name: str = Field(..., description="Skill 唯一标识, 例如 host_resource_diagnosis 或 github-pr-workflow")
    display_name: str = Field(..., description="人类可读名称, 用于日志和前端展示")
    description: str = Field(..., description="适用场景一句话描述, 给 Skill Router 看")
    category: str = Field(default="", description="Skill 分类, 可来自 metadata.hermes.category")
    platforms: List[str] = Field(
        default_factory=list,
        description="兼容平台: windows / linux / macos; 空列表表示全平台",
    )
    tags: List[str] = Field(default_factory=list, description="标签, 可来自 metadata.hermes.tags")
    triggers: List[str] = Field(
        default_factory=list,
        description="触发关键字, 用于启发式匹配 (本期仅作 Router 提示, 不参与硬匹配)",
    )
    allowed_tools: List[str] = Field(
        default_factory=list,
        description="允许 Executor 调用的工具白名单. 第一版仅作记录, Harness 阶段强制",
    )
    risk_level: RiskLevel = Field(
        default="low",
        description="风险等级, Harness 用于决定是否需要人工确认",
    )

    # ===== Markdown body =====
    playbook: str = Field(
        default="",
        description="完整 Markdown body, 包含适用场景/推荐排查步骤/输出格式等",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="原始/扩展 metadata, 兼容 Hermes metadata.hermes.*",
    )
    linked_files: List[str] = Field(
        default_factory=list,
        description="Skill 目录下除 SKILL.md 外的支持文件相对路径",
    )
    source_path: Optional[str] = Field(default=None, description="源 SKILL.md 文件路径")
    source_root: Optional[str] = Field(default=None, description="扫描来源根目录")

    @field_validator("name")
    @classmethod
    def _name_snake_case(cls, v: str) -> str:
        if not v or not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(f"skill name 仅允许字母数字、下划线和短横线: {v!r}")
        return v.lower()

    @field_validator("platforms", "tags", mode="before")
    @classmethod
    def _normalize_str_list(cls, v: object) -> list[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [item.strip().lower() for item in v.split(",") if item.strip()]
        if isinstance(v, list):
            return [str(item).strip().lower() for item in v if str(item).strip()]
        return []

    def to_router_card(self) -> str:
        """生成给 Skill Router LLM 看的菜单条目 (Markdown)."""
        triggers = ", ".join(self.triggers) if self.triggers else "(无)"
        return (
            f"- **{self.name}** — {self.display_name}\n"
            f"  适用场景: {self.description}\n"
            f"  触发关键字: {triggers}"
        )

    def to_summary(self) -> dict[str, Any]:
        """生成 API/前端可用的精简元信息."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category,
            "platforms": self.platforms,
            "tags": self.tags,
            "triggers": self.triggers,
            "allowed_tools": self.allowed_tools,
            "risk_level": self.risk_level,
            "source_path": self.source_path,
            "linked_files": self.linked_files,
        }
