"""SkillRegistry: 启动时扫描 definitions/, 加载所有 SKILL.md, 全局单例.

设计:
  - 文件布局: app/skills/definitions/<skill_name>/SKILL.md
  - 进程级 lru_cache 单例 (启动时加载一次, 后续从内存取)
  - 强制要求兜底 Skill `generic_oncall` 存在, 保证 Router 永远有 fallback
"""

from __future__ import annotations

import os
import platform
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from app.config import settings
from app.skills.loader import SkillLoadError, load_skill_from_file
from app.skills.models import Skill

# Skill 定义目录: app/skills/definitions/<skill_name>/SKILL.md
_DEFINITIONS_DIR = Path(__file__).parent / "definitions"

# 兜底 Skill 名: Router 选不出来时使用
GENERIC_SKILL_NAME = "generic_oncall"
# M10 Tier2: _drafts/ 存放 graduation_worker 生成的 SKILL.md 草稿,
# 必须经治理 API 显式 activate 才移到 definitions/ —— registry 永远不扫 _drafts/。
_IGNORED_DIRS = {".git", ".github", ".hub", ".archive", "__pycache__", "_drafts"}


class SkillRegistry:
    """加载和管理所有 Skill."""

    def __init__(self, skills: Dict[str, Skill]) -> None:
        self._skills = skills

    def all(self) -> List[Skill]:
        return list(self._skills.values())

    def names(self) -> List[str]:
        return list(self._skills.keys())

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def get_or_generic(self, name: Optional[str]) -> Skill:
        """取指定 Skill, 不存在时回退到 generic_oncall.

        Raises:
            RuntimeError: 兜底 Skill 也缺失 (规约错误)
        """
        if name and name in self._skills:
            return self._skills[name]
        generic = self._skills.get(GENERIC_SKILL_NAME)
        if generic is None:
            raise RuntimeError(
                f"兜底 Skill {GENERIC_SKILL_NAME!r} 缺失, "
                f"请确认 app/skills/definitions/{GENERIC_SKILL_NAME}/SKILL.md 存在"
            )
        return generic

    def to_router_menu(self) -> str:
        """生成给 Router LLM 看的全部 Skill 菜单 (Markdown)."""
        cards = [s.to_router_card() for s in self._skills.values()]
        return "\n\n".join(cards)

    def read_supporting_file(self, name: str, file_path: str) -> str:
        """读取某个 Skill 目录内的支持文件, 带路径逃逸保护."""
        skill = self.get(name)
        if not skill or not skill.source_path:
            raise FileNotFoundError(f"Skill not found: {name}")
        base = Path(skill.source_path).parent.resolve()
        target = (base / file_path).resolve()
        if target == Path(skill.source_path).resolve():
            return target.read_text(encoding="utf-8")
        if base not in target.parents:
            raise ValueError("file_path must stay inside the skill directory")
        if not target.is_file():
            raise FileNotFoundError(file_path)
        return target.read_text(encoding="utf-8")


def _split_config_list(value: str) -> list[str]:
    if not value:
        return []
    raw = value.replace(os.pathsep, ",").replace("\n", ",")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _current_platform() -> str:
    configured = (settings.skills_platform or "").strip().lower()
    if configured:
        return configured
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    if system.startswith("win"):
        return "windows"
    if system.startswith("linux"):
        return "linux"
    return system


def _is_platform_enabled(skill: Skill, current: str) -> bool:
    return not skill.platforms or current in set(skill.platforms)


def _iter_skill_files(root: Path) -> list[Path]:
    if not root.exists():
        logger.warning(f"[Skill] 定义目录不存在: {root}")
        return []
    result: list[Path] = []
    for skill_md in sorted(root.rglob("SKILL.md")):
        rel_parts = skill_md.relative_to(root).parts
        if any(part in _IGNORED_DIRS for part in rel_parts):
            continue
        result.append(skill_md)
    return result


def _skill_roots() -> list[Path]:
    roots = [_DEFINITIONS_DIR]
    for item in _split_config_list(settings.skills_external_dirs):
        roots.append(Path(item).expanduser())
    return roots


def _scan_definitions() -> Dict[str, Skill]:
    """扫描内置 definitions/ 与可选外部目录中的所有 SKILL.md."""
    skills: Dict[str, Skill] = {}
    disabled = {name.lower() for name in _split_config_list(settings.skills_disabled)}
    current_platform = _current_platform()

    for root in _skill_roots():
        for skill_md in _iter_skill_files(root):
            try:
                skill = load_skill_from_file(skill_md, root=root)
            except SkillLoadError as e:
                logger.error(f"[Skill] 跳过 {skill_md}: {e}")
                continue

            if skill.name in disabled:
                logger.info(f"[Skill] 已禁用 {skill.name!r}: {skill_md}")
                continue
            if not _is_platform_enabled(skill, current_platform):
                logger.info(
                    f"[Skill] 平台不匹配, 跳过 {skill.name!r}: "
                    f"platforms={skill.platforms}, current={current_platform}"
                )
                continue

            if skill.name in skills:
                logger.warning(
                    f"[Skill] 重名 {skill.name!r}, 后者覆盖前者: {skill_md}"
                )
            skills[skill.name] = skill

    return skills


@lru_cache(maxsize=1)
def get_skill_registry() -> SkillRegistry:
    """获取全局 SkillRegistry 单例 (启动时加载一次)."""
    skills = _scan_definitions()
    logger.info(
        f"[Skill] 已加载 {len(skills)} 个 Skill: {list(skills.keys())}"
    )
    if GENERIC_SKILL_NAME not in skills:
        logger.warning(
            f"[Skill] 兜底 Skill {GENERIC_SKILL_NAME!r} 缺失, Router 失败时无法回退"
        )
    return SkillRegistry(skills)


def reload_skill_registry() -> SkillRegistry:
    """清空缓存并重新扫描 Skill, 用于本地调试/新增 SKILL.md 后热加载."""
    get_skill_registry.cache_clear()
    return get_skill_registry()
