"""Skill 列表查询接口.

GET /api/v1/skills
  -> 列出全部已注册 Skill 的元信息, 供前端展示 Playbook 库
GET /api/v1/skills/{name}
  -> 查看单个 Skill 全文和支持文件索引

列表接口不返回 playbook 全文, 避免响应体过大.
"""

from typing import Any, List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.schemas.common import ApiResponse
from app.skills import get_skill_registry, reload_skill_registry

router = APIRouter(prefix="/skills", tags=["skills"])


class SkillSummary(BaseModel):
    """Skill 给前端看的精简元信息."""

    name: str = Field(..., description="Skill 唯一标识")
    display_name: str = Field(..., description="人类可读名称")
    description: str = Field(..., description="一句话适用场景")
    category: str = Field(default="", description="分类")
    platforms: List[str] = Field(default_factory=list, description="兼容平台")
    tags: List[str] = Field(default_factory=list, description="标签")
    triggers: List[str] = Field(default_factory=list, description="触发关键字")
    allowed_tools: List[str] = Field(default_factory=list, description="允许调用的工具白名单")
    risk_level: str = Field(..., description="风险等级: low / medium / high")
    context: str = Field(default="inline", description="执行模式: inline / fork")
    source_path: str | None = Field(default=None, description="源 SKILL.md 路径")
    linked_files: List[str] = Field(default_factory=list, description="支持文件相对路径")


class SkillListData(BaseModel):
    """Skill 列表响应载荷."""

    total: int = Field(..., description="Skill 总数")
    skills: List[SkillSummary] = Field(default_factory=list, description="全部 Skill 元信息")


class SkillDetailData(SkillSummary):
    """单个 Skill 详情."""

    playbook: str = Field(default="", description="SKILL.md Markdown body")
    metadata: dict[str, Any] = Field(default_factory=dict, description="扩展 metadata")


class SkillFileData(BaseModel):
    """Skill 支持文件内容."""

    name: str = Field(..., description="Skill name")
    path: str = Field(..., description="Skill 目录内的相对路径")
    content: str = Field(default="", description="文件内容")


def _summary_from_skill(skill) -> SkillSummary:
    return SkillSummary(**skill.to_summary())


@router.get(
    "",
    response_model=ApiResponse[SkillListData],
    summary="列出全部已注册 Skill",
    description=(
        "返回当前 SkillRegistry 中已加载的全部 Skill 元信息 (不含 playbook 全文).\n\n"
        "Skill 会从内置 `app/skills/definitions/**/SKILL.md` 和可选 `SKILLS_EXTERNAL_DIRS` 加载."
    ),
)
async def list_skills() -> ApiResponse[SkillListData]:
    registry = get_skill_registry()
    summaries = [_summary_from_skill(s) for s in registry.all()]
    return ApiResponse.success(
        data=SkillListData(total=len(summaries), skills=summaries),
        message=f"已加载 {len(summaries)} 个 Skill",
    )


@router.post(
    "/reload",
    response_model=ApiResponse[SkillListData],
    summary="重新加载 SkillRegistry",
    description="清空进程内 SkillRegistry 缓存并重新扫描内置与外部 SKILL.md.",
)
async def reload_skills() -> ApiResponse[SkillListData]:
    registry = reload_skill_registry()
    summaries = [_summary_from_skill(s) for s in registry.all()]
    return ApiResponse.success(
        data=SkillListData(total=len(summaries), skills=summaries),
        message=f"已重新加载 {len(summaries)} 个 Skill",
    )


@router.get(
    "/{name}",
    response_model=ApiResponse[SkillDetailData],
    summary="查看单个 Skill",
    description="返回单个 Skill 的元信息、playbook 全文和支持文件索引.",
)
async def get_skill(name: str) -> ApiResponse[SkillDetailData]:
    skill = get_skill_registry().get(name.lower())
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill not found: {name}")
    return ApiResponse.success(
        data=SkillDetailData(
            **skill.to_summary(),
            playbook=skill.playbook,
            metadata=skill.metadata,
        ),
        message=f"已加载 Skill: {skill.name}",
    )


@router.get(
    "/{name}/files",
    response_model=ApiResponse[SkillFileData],
    summary="读取 Skill 支持文件",
    description="读取某个 Skill 目录内的相对路径文件; 默认读取 SKILL.md.",
)
async def get_skill_file(
    name: str,
    path: str = Query(default="SKILL.md", description="Skill 目录内相对路径"),
) -> ApiResponse[SkillFileData]:
    registry = get_skill_registry()
    try:
        content = registry.read_supporting_file(name.lower(), path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ApiResponse.success(
        data=SkillFileData(name=name.lower(), path=path, content=content),
        message="ok",
    )
