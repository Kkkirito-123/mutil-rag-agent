"""SKILL.md 解析器.

格式: YAML frontmatter + Markdown body.
  - 文件以 `---` 开头
  - 中间是 YAML 元信息
  - 第二个 `---` 之后是 Markdown 正文 (作为 Skill.playbook)

依赖:
  - PyYAML (轻量, LangChain 也间接依赖)

失败处理:
  - 解析异常一律抛 SkillLoadError, 由 registry 捕获并跳过该文件
  - 不让单个坏文件阻塞整个启动
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml
from loguru import logger

from app.skills.models import Skill


class SkillLoadError(Exception):
    """SKILL.md 解析失败."""


# 匹配 ^---\n<frontmatter>\n---\n<body>$
_FRONTMATTER_RE = re.compile(
    r"^---\s*\n(.*?)\n---\s*\n(.*)$",
    re.DOTALL,
)
_IGNORED_DIRS = {".git", ".github", ".hub", ".archive", "__pycache__", "_drafts"}


def _split_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    """把 SKILL.md 文本拆为 (frontmatter dict, body str)."""
    # 去 BOM, 防 Windows 用 UTF-8 BOM 保存
    cleaned = text.lstrip("\ufeff")
    match = _FRONTMATTER_RE.match(cleaned)
    if not match:
        raise SkillLoadError(
            "未找到 YAML frontmatter, SKILL.md 必须以 `---` 开头并以 `---` 结束 frontmatter 段"
        )
    fm_text, body = match.group(1), match.group(2)
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as e:
        raise SkillLoadError(f"frontmatter YAML 语法错误: {e}") from e
    if not isinstance(fm, dict):
        raise SkillLoadError(f"frontmatter 必须是字典, 实际是 {type(fm).__name__}")
    return fm, body.strip()


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _title_from_body(body: str) -> str:
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return ""


def _category_from_path(path: Path, root: Path | None) -> str:
    if not root:
        return path.parent.parent.name if path.parent.parent != path.parent else ""
    try:
        parts = path.parent.relative_to(root).parts
    except ValueError:
        return ""
    return parts[0] if len(parts) > 1 else ""


def _linked_files(path: Path) -> list[str]:
    base = path.parent
    files: list[str] = []
    for child in sorted(base.rglob("*")):
        if not child.is_file():
            continue
        if child.name == "SKILL.md":
            continue
        if any(part in _IGNORED_DIRS for part in child.relative_to(base).parts):
            continue
        files.append(child.relative_to(base).as_posix())
        if len(files) >= 100:
            break
    return files


def load_skill_from_file(path: Path, *, root: Path | None = None) -> Skill:
    """从 SKILL.md 文件加载单个 Skill.

    Args:
        path: SKILL.md 的绝对路径

    Returns:
        Skill 实例

    Raises:
        SkillLoadError: frontmatter 缺失/字段非法/YAML 语法错误
    """
    text = path.read_text(encoding="utf-8")
    fm, body = _split_frontmatter(text)
    fm = dict(fm)
    metadata = fm.get("metadata") if isinstance(fm.get("metadata"), dict) else {}
    hermes_meta = metadata.get("hermes") if isinstance(metadata.get("hermes"), dict) else {}

    skill_name = str(fm.get("name") or path.parent.name).strip()
    display_name = str(
        fm.get("display_name")
        or fm.get("title")
        or _title_from_body(body)
        or skill_name.replace("-", " ").replace("_", " ").title()
    ).strip()
    category = str(
        fm.get("category")
        or hermes_meta.get("category")
        or _category_from_path(path, root)
        or ""
    ).strip()
    tags = _as_list(fm.get("tags") or hermes_meta.get("tags"))

    fm["name"] = skill_name
    fm["display_name"] = display_name
    fm["description"] = str(fm.get("description") or display_name).strip()
    fm["category"] = category
    fm["tags"] = tags
    fm["metadata"] = metadata
    fm["linked_files"] = _linked_files(path)

    try:
        skill = Skill(
            **fm,
            playbook=body,
            source_path=str(path),
            source_root=str(root) if root else None,
        )
    except Exception as e:
        # Pydantic ValidationError 也走这里, 统一包成 SkillLoadError
        raise SkillLoadError(f"Skill 字段校验失败 ({path}): {e}") from e

    logger.debug(f"[Skill] 已加载: {skill.name} ({skill.display_name}) <- {path}")
    return skill
