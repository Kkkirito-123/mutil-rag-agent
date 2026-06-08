"""LLM Wiki 只读 API (经验沉淀展示).

把 data/wiki/ 暴露给前端"经验库" Tab, 让用户看到:
  - 现有故障模式 / 服务页
  - 最近哪些诊断 ingest 进了哪一页 (log.md)
  - 单页内容 (包含 [[wikilink]] 互链)

只读: 写操作 (新增页面) 由 ingest_diagnosis 自动完成, 不暴露 API 防被滥用.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.wiki.store import _WIKI_DIR  # 复用同一个根目录定义

router = APIRouter(prefix="/wiki", tags=["wiki"])

_LOG_LINE_RE = re.compile(r"^## \[(?P<date>\d{4}-\d{2}-\d{2})\]\s*(?P<body>.*)$")
_CATEGORIES = ("services", "patterns")


def _safe_page_path(category: str, slug: str) -> Path:
    if category not in _CATEGORIES:
        raise HTTPException(status_code=400, detail="非法 category, 仅支持 services / patterns")
    # slug 只允许字母数字下划线短横
    if not re.fullmatch(r"[a-z0-9_\-]{1,80}", slug or ""):
        raise HTTPException(status_code=400, detail="非法 slug")
    p = (_WIKI_DIR / category / f"{slug}.md").resolve()
    base = (_WIKI_DIR / category).resolve()
    if base not in p.parents:
        raise HTTPException(status_code=400, detail="路径越界")
    return p


def _stat(p: Path) -> dict[str, Any]:
    try:
        st = p.stat()
        return {
            "size_bytes": st.st_size,
            "modified_at": datetime.fromtimestamp(st.st_mtime).isoformat(),
        }
    except Exception:
        return {"size_bytes": 0, "modified_at": None}


@router.get("/overview", summary="Wiki 总览 (是否启用 + 页面计数)")
async def wiki_overview() -> dict[str, Any]:
    enabled = bool(settings.wiki_enabled)
    out: dict[str, Any] = {
        "enabled": enabled,
        "recall_enabled": bool(settings.wiki_recall_enabled),
        "wiki_dir": str(_WIKI_DIR),
        "exists": _WIKI_DIR.exists(),
        "pages": {},
    }
    if not _WIKI_DIR.exists():
        return out
    for cat in _CATEGORIES:
        d = _WIKI_DIR / cat
        if not d.exists():
            out["pages"][cat] = 0
            continue
        out["pages"][cat] = sum(1 for _ in d.glob("*.md"))
    out["index_exists"] = (_WIKI_DIR / "index.md").exists()
    out["log_exists"] = (_WIKI_DIR / "log.md").exists()
    return out


@router.get("/pages", summary="列出所有 wiki 页面")
async def list_pages(
    category: str | None = Query(None, description="可选 services / patterns"),
    limit: int = Query(200, ge=1, le=1000),
) -> dict[str, Any]:
    if not _WIKI_DIR.exists():
        return {"count": 0, "items": []}
    cats = [category] if category else list(_CATEGORIES)
    items: list[dict[str, Any]] = []
    for cat in cats:
        if cat not in _CATEGORIES:
            continue
        d = _WIKI_DIR / cat
        if not d.exists():
            continue
        for p in d.glob("*.md"):
            meta = _stat(p)
            preview = ""
            try:
                txt = p.read_text(encoding="utf-8")
                # 取第一行非空作为预览
                for ln in txt.splitlines():
                    s = ln.strip()
                    if s:
                        preview = s.lstrip("#").strip()[:160]
                        break
            except Exception:
                pass
            items.append({
                "category": cat,
                "slug": p.stem,
                "ref": f"{cat}/{p.stem}",
                "preview": preview,
                **meta,
            })
    items.sort(key=lambda x: (x.get("modified_at") or ""), reverse=True)
    return {"count": len(items), "items": items[:limit]}


@router.get("/pages/{category}/{slug}", summary="读取单个 wiki 页 (markdown 原文)")
async def get_page(category: str, slug: str) -> dict[str, Any]:
    p = _safe_page_path(category, slug)
    if not p.is_file():
        raise HTTPException(status_code=404, detail="page not found")
    try:
        content = p.read_text(encoding="utf-8")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"读取失败: {exc}")
    return {
        "category": category,
        "slug": slug,
        "ref": f"{category}/{slug}",
        "content": content,
        **_stat(p),
    }


@router.get("/index", summary="Wiki 索引页 (index.md)")
async def get_index() -> dict[str, Any]:
    p = _WIKI_DIR / "index.md"
    if not p.exists():
        return {"content": "", "exists": False}
    return {"exists": True, "content": p.read_text(encoding="utf-8"), **_stat(p)}


@router.get("/log", summary="最近的 ingest 流水 (log.md)")
async def get_log(limit: int = Query(50, ge=1, le=500)) -> dict[str, Any]:
    p = _WIKI_DIR / "log.md"
    if not p.exists():
        return {"count": 0, "items": []}
    lines = p.read_text(encoding="utf-8").splitlines()
    entries: list[dict[str, Any]] = []
    for ln in reversed(lines):
        m = _LOG_LINE_RE.match(ln.strip())
        if not m:
            continue
        entries.append({"date": m.group("date"), "entry": m.group("body").strip()})
        if len(entries) >= limit:
            break
    return {"count": len(entries), "items": entries}
