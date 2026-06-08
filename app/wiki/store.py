"""Karpathy「LLM Wiki」模式的 AIOps 落地: 让 LLM 增量维护一组互链的 markdown 页面。

原版 (https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 的主张:
**别用 RAG 每次从原始文档重检索, 而让 LLM 持续维护一个结构化、互链的 wiki** ——
知识是"合并沉淀"而非"每次重查"。本模块把它搬到诊断场景:

  - 每次诊断 = 一篇被 ingest 的"来源";
  - LLM 读相关页 -> **合并/更新** 根因/修复 -> 用 `[[...]]` 互链, 而不是 append 新行;
  - 维护 `index.md` 目录 + `log.md` 流水;
  - 召回时 **先读 index 再钻进页面** (read-index-first), 不靠 embedding。

与原版的取舍差异 (诚实标注):
  - 原版是 human+agent 交互维护; 这里是诊断收尾**自动** ingest (无人在环),
    故合并完全交给 LLM + 确定性兜底 (LLM 不可用时仍把这次诊断追加进 pattern 页);
  - asyncio.Lock + fcntl 文件锁串行化写, API 多进程与多个 Worker 共享目录时也不会互踩。

容错: ingest / recall 任何异常都吞掉, 绝不拖垮诊断主链路。
"""

from __future__ import annotations

import asyncio
import fcntl
import re
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, TextIO

from loguru import logger

from app.config import settings
from app.core.llm import get_chat_llm
from app.core.llm_parse import extract_json

# data/wiki/ 在仓库根下 (app/wiki/store.py -> parents[2] = repo root)
_WIKI_DIR = Path(__file__).resolve().parents[2] / "data" / "wiki"
_SERVICES = _WIKI_DIR / "services"
_PATTERNS = _WIKI_DIR / "patterns"
_INDEX = _WIKI_DIR / "index.md"
_LOG = _WIKI_DIR / "log.md"
_LOCK_FILE = _WIKI_DIR / ".write.lock"

_write_lock = asyncio.Lock()  # 单进程内串行化 wiki 写, 防并行诊断互踩同页

_SLUG_RE = re.compile(r"[^a-z0-9]+")
_CJK = re.compile(r"[一-鿿]")
_WORD = re.compile(r"[a-z0-9_]{2,}")
_WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")


def _slug(text: Any, fallback: str = "unknown") -> str:
    s = _SLUG_RE.sub("-", str(text or "").lower()).strip("-")
    return (s or fallback)[:64]


def _tokenize(text: Any) -> set[str]:
    s = str(text or "").lower()
    return set(_WORD.findall(s)) | set(_CJK.findall(s))


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8") if p.exists() else ""
    except Exception:
        return ""


def _write(p: Path, content: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")


@asynccontextmanager
async def _wiki_write_guard() -> AsyncIterator[None]:
    """Serialize Wiki read/merge/write across API processes and workers."""
    handle: TextIO | None = None
    async with _write_lock:
        try:
            _WIKI_DIR.mkdir(parents=True, exist_ok=True)
            handle = await asyncio.to_thread(_LOCK_FILE.open, "a+", encoding="utf-8")
            await asyncio.to_thread(fcntl.flock, handle.fileno(), fcntl.LOCK_EX)
            yield
        finally:
            if handle is not None:
                await asyncio.to_thread(fcntl.flock, handle.fileno(), fcntl.LOCK_UN)
                handle.close()


def _coerce_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                parts.append(str(block.get("text") or block.get("content") or ""))
        return "".join(parts)
    return str(content or "")


def _parse_target(signature: str, query: str) -> tuple[str, str]:
    """从 alert_signature ("alertname|service") 解析出 (service, pattern_slug)。

    手动诊断无 signature 时, service 留空、pattern 用 query 关键词派生。
    """
    service = ""
    if signature and "|" in signature:
        service = signature.split("|", 1)[1].strip()
    pattern_slug = _slug(signature or query, fallback="incident")
    return service, pattern_slug


# ==================== index / log 维护 ====================

def _update_index(page_ref: str, summary: str) -> None:
    """把一行 `- [[page_ref]] — summary` 并入 index.md (同 ref 去重更新)。"""
    summary = " ".join(str(summary or "").split())[:100] or page_ref
    line = f"- [[{page_ref}]] — {summary}"
    body = [ln for ln in _read(_INDEX).splitlines() if ln.startswith("- [[")]
    body = [ln for ln in body if f"[[{page_ref}]]" not in ln]
    body.append(line)
    _write(_INDEX, "# Wiki 目录\n\n" + "\n".join(sorted(body)))


def _append_log(entry: str) -> None:
    """append-only 流水, 每行 `## [date] entry` (原版 log.md 约定, 可被 unix 工具解析)。"""
    line = f"## [{_now()}] {' '.join(str(entry or '').split())}"
    _write(_LOG, (_read(_LOG).rstrip("\n") + "\n" + line) if _read(_LOG) else line)


# ==================== 写: ingest 一次诊断 ====================

_INGEST_SYS = (
    "你在维护一个事故知识 Wiki (Karpathy LLM Wiki 模式)。给你一次诊断的报告, 以及两张相关"
    " markdown 页面的**现有内容**(可能为空=新页)。把这次诊断的**现象/根因/修复**合并进页面:\n"
    "- 同类信息**更新**而非重复堆叠; 用 `[[services/x]]` / `[[patterns/y]]` 互链;\n"
    "- 页面保持精炼、分节(## 现象 / ## 根因 / ## 处置 / ## 关联); service 页汇总该服务的多类故障。\n"
    "只输出一个 JSON 对象, 不要解释或围栏:\n"
    '{"service_page": "<service 页整页 markdown, 无 service 则空串>",\n'
    ' "pattern_page": "<pattern 页整页 markdown>",\n'
    ' "index_summary": "<pattern 页一行摘要, <=80字>",\n'
    ' "log_line": "<一行流水, 如: checkout redis 超时 -> 连接池耗尽>"}'
)


async def ingest_diagnosis(
    *,
    query: str,
    report_text: str,
    signature: str = "",
    session_id: str = "",
    mode: str = "fast",
) -> bool:
    """把一次诊断 ingest 进 wiki: LLM 合并相关页 + 更新 index + append log。best-effort。"""
    if not settings.wiki_enabled:
        return False
    try:
        async with _wiki_write_guard():
            service, pat = _parse_target(signature, query)
            svc_path = (_SERVICES / f"{_slug(service)}.md") if service else None
            pat_path = _PATTERNS / f"{pat}.md"
            existing_svc = _read(svc_path) if svc_path else ""
            existing_pat = _read(pat_path)

            try:
                model = settings.wiki_summary_model or settings.dashscope_router_model
                user = (
                    f"# 本次诊断\n诉求: {str(query or '')[:400]}\n\n报告:\n{str(report_text or '')[:3000]}\n\n"
                    f"# 现有 service 页 ({'services/' + _slug(service) if service else '无'})\n{existing_svc or '(新页/无)'}\n\n"
                    f"# 现有 pattern 页 (patterns/{pat})\n{existing_pat or '(新页)'}"
                )
                llm = get_chat_llm(model=model, temperature=0.0, timeout=60.0)
                resp = await llm.ainvoke([("system", _INGEST_SYS), ("human", user)])
                parsed = extract_json(_coerce_text(getattr(resp, "content", "")), source="wiki ingest")
                svc_md = str(parsed.get("service_page") or existing_svc).strip()
                pat_md = str(parsed.get("pattern_page") or "").strip()
                index_summary = str(parsed.get("index_summary") or "").strip()
                log_line = str(parsed.get("log_line") or "").strip()
            except Exception as exc:
                # LLM 不可用 -> 确定性兜底: 把本次诊断追加进 pattern 页 (退化成 append, 但闭环不断)
                logger.warning(f"[wiki] LLM 合并失败, 走确定性兜底: {type(exc).__name__}: {exc}")
                svc_md = existing_svc
                entry = f"\n## [{_now()}] {mode}\n- 现象: {str(query or '')[:200]}\n"
                pat_md = ((existing_pat.rstrip() + entry) if existing_pat else f"# 故障模式: {pat}\n{entry}").strip()
                index_summary = (query or pat)[:80]
                log_line = f"{mode} | {pat}"

            if not pat_md:
                return False
            if svc_path and svc_md:
                _write(svc_path, svc_md)
            _write(pat_path, pat_md)
            _update_index(f"patterns/{pat}", index_summary or pat)
            if service and svc_md:
                _update_index(f"services/{_slug(service)}", f"服务 {service} 的故障知识汇总")
            _append_log(f"diagnosis | {log_line or pat}")
        logger.info(
            f"[wiki] ingested -> patterns/{pat}.md"
            + (f" + services/{_slug(service)}.md" if (svc_path and svc_md) else "")
        )
        return True
    except Exception as exc:
        logger.warning(f"[wiki] ingest 失败, 跳过 (不影响诊断): {type(exc).__name__}: {exc}")
        return False


# ==================== 读: read-index-first 召回 ====================

async def recall_block(*, query: str = "", signature: str = "", limit_chars: int | None = None) -> str:
    """召回相关 wiki 页拼成注入块; 无则空串。best-effort。

    原版 read-index-first: 优先命中 service/pattern 直达页; 否则读 index.md 按关键词
    挑相关页再钻进去。
    """
    if not settings.wiki_enabled or not settings.wiki_recall_enabled:
        return ""
    try:
        service, pat = _parse_target(signature, query)
        max_chars = limit_chars if limit_chars is not None else settings.wiki_recall_max_chars
        pages: list[Path] = []

        # ① 直达: service 页 + pattern 页
        if service:
            sp = _SERVICES / f"{_slug(service)}.md"
            if sp.exists():
                pages.append(sp)
        pp = _PATTERNS / f"{pat}.md"
        if pp.exists():
            pages.append(pp)

        # ② 兜底: 读 index, 按 query 与目录行的关键词重叠挑 top-2 页
        if not pages:
            qt = _tokenize(query)
            scored: list[tuple[int, str]] = []
            for ln in _read(_INDEX).splitlines():
                m = _WIKILINK.search(ln)
                if not m:
                    continue
                score = len(qt & _tokenize(ln))
                if score > 0:
                    scored.append((score, m.group(1)))
            scored.sort(key=lambda x: x[0], reverse=True)
            for _, ref in scored[:2]:
                p = _WIKI_DIR / f"{ref}.md"
                if p.exists():
                    pages.append(p)

        blocks: list[str] = []
        seen: set[str] = set()
        for p in pages:
            key = str(p)
            if key in seen:
                continue
            seen.add(key)
            txt = _read(p).strip()
            if txt:
                blocks.append(f"### {p.relative_to(_WIKI_DIR)}\n{txt}")
        out = "\n\n".join(blocks)[:max_chars].strip()
        if out:
            logger.info(f"[wiki] 召回 {len(blocks)} 页注入诊断 (read-index-first)")
        return out
    except Exception as exc:
        logger.warning(f"[wiki] 召回失败, 跳过 (不影响诊断): {type(exc).__name__}: {exc}")
        return ""


# ==================== 维护: 结构化 lint (确定性, 不需 LLM) ====================

def lint() -> dict[str, list[str]]:
    """结构健康检查 (原版 lint 的确定性子集): 孤页 / 未入 index / 空页。

    LLM 版的"矛盾/过期"检查留作 scripts/wiki_lint.py 的可选增强。
    """
    findings: dict[str, list[str]] = {"orphan": [], "not_in_index": [], "empty": []}
    if not _WIKI_DIR.exists():
        return findings
    index_text = _read(_INDEX)
    all_links = set(_WIKILINK.findall(index_text))
    for sub in ("services", "patterns"):
        d = _WIKI_DIR / sub
        if not d.exists():
            continue
        for p in d.glob("*.md"):
            ref = f"{sub}/{p.stem}"
            body = _read(p).strip()
            if not body:
                findings["empty"].append(ref)
            if ref not in all_links:
                findings["not_in_index"].append(ref)
            # 孤页: 没有任何其它页指向它 (粗略: 全 wiki 文本里没有 [[ref]])
            inbound = sum(
                1 for q in d.parent.rglob("*.md")
                if q != p and f"[[{ref}]]" in _read(q)
            )
            if inbound == 0:
                findings["orphan"].append(ref)
    return findings
