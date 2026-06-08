"""文档分块器: Parent-Child + 结构保护 (参考腾讯 WeKnora 设计)。

切分策略 (3 步):
  1. MarkdownHeaderTextSplitter 按 # ## ### 切, 得到天然的"父块"候选 (节级)
  2. 父块若超 rag_parent_max_chars, 按结构保护规则二次切成多个父块
  3. 每个父块再切 child 小块 (rag_chunk_size); child 带 parent_id + parent_content

为什么 Parent-Child:
  - child 小 (~300 字), embedding 聚焦 → 召回精度高
  - parent 大 (≤2400 字), 完整段落供 LLM 上下文不缺失
  - retrieval 命中 child → 按 parent_id 去重 → 返回 parent_content

为什么结构保护:
  - markdown 表格/代码块/链接/LaTeX 被切到一半会让 LLM 读到无效片段
  - 切之前用占位符替换保护区, 切完还原 → 保证保护区永不被切碎
  - 6 种 regex 模式参考腾讯 WeKnora 生产实践

embedding 增强 (沿用上一版亮点):
  - 章节路径 [h1/h2/h3] 拼到 child page_content 最前面参与 embedding
  - 离线实测: R@1 从 83.33% → 91.67% (+10%), MRR 0.88 → 0.94
"""

from __future__ import annotations

import hashlib
import re
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from loguru import logger

from app.config import settings

# Markdown 标题层级 → metadata 字段名 (用于章节追踪)
_HEADERS_TO_SPLIT_ON = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
]

# 结构保护: 在这些 regex 区间内绝不切 (参考腾讯 WeKnora 6 种模式)
_PROTECTED_PATTERNS = [
    r"```[\s\S]*?```",                                       # 代码块 (含语言标识)
    r"\|[^\n]*\|\n\|[\s\-:|]+\|(?:\n\|[^\n]*\|)*",            # markdown 表格 (表头 + 分隔行 + 数据行)
    r"!\[[^\]]*\]\([^)]+\)",                                  # 图片链接 ![alt](url)
    r"\[[^\]\n]+\]\([^)\n]+\)",                               # 普通链接 [text](url)
    r"\$\$[\s\S]*?\$\$",                                      # 块级 LaTeX 公式
    r"\$[^$\n]+\$",                                           # 行内 LaTeX 公式
]


def _find_protected_spans(text: str) -> list[tuple[int, int]]:
    """找所有不可切的 (start, end) 区间, 重叠合并。"""
    spans: list[tuple[int, int]] = []
    for pat in _PROTECTED_PATTERNS:
        for m in re.finditer(pat, text):
            spans.append((m.start(), m.end()))
    if not spans:
        return []
    spans.sort()
    merged: list[tuple[int, int]] = [spans[0]]
    for s, e in spans[1:]:
        ps, pe = merged[-1]
        if s <= pe:
            merged[-1] = (ps, max(pe, e))
        else:
            merged.append((s, e))
    return merged


def _placeholder(i: int) -> str:
    """无分隔符占位 token; RecursiveCharacterTextSplitter 不会从中间切。

    用零宽空格 \\u200B 包裹纯字母数字, 长度 <14 字符, 小于任何合理 chunk_size;
    且不含切刀偏好的分隔符 (\\n / 。 / 空格), 因此切刀不会在它内部切断。
    """
    return f"​PROT{i:04d}​"


def _protect_and_split(text: str, splitter: RecursiveCharacterTextSplitter) -> list[str]:
    """用 splitter 切 text, 但保护区永不被切碎: 替换占位符 → 切 → 还原。"""
    spans = _find_protected_spans(text)
    if not spans:
        return splitter.split_text(text)

    placeholders: dict[str, str] = {}
    parts: list[str] = []
    last = 0
    for i, (s, e) in enumerate(spans):
        parts.append(text[last:s])
        token = _placeholder(i)
        placeholders[token] = text[s:e]
        parts.append(token)
        last = e
    parts.append(text[last:])
    raw_chunks = splitter.split_text("".join(parts))

    restored: list[str] = []
    for c in raw_chunks:
        for tok, orig in placeholders.items():
            if tok in c:
                c = c.replace(tok, orig)
        restored.append(c)
    return restored


def _parent_id(content: str) -> str:
    """父块内容哈希 → 稳定 id (12 位 hex, 足够区分万级父块)。"""
    return hashlib.md5(content.encode("utf-8")).hexdigest()[:12]


def split_markdown(content: str, source: str) -> List[Document]:
    """把 Markdown 切成 child Document chunks (parent-child + 结构保护)。

    Args:
        content: Markdown 全文
        source:  来源标识 (通常是文件名), 写入 metadata

    Returns:
        List[Document]: 每个 Document 是 child 块, metadata 含:
          - source         来源文件名
          - chapter        h1/h2/h3 拼成的章节路径
          - parent_id      所属父块的稳定 hash id (12 位 hex)
          - parent_content 父块完整文本 (retrieval 命中 child 后返给 LLM 的就是它)
          - chunk_index    全局 child 序号
          - h1/h2/h3       各级标题原始文本
        Child page_content 已注入章节前缀 (供 embedding)。
    """
    if not content.strip():
        logger.warning(f"split_markdown: 空内容 source={source}")
        return []

    parent_max = max(500, int(settings.rag_parent_max_chars or 2400))
    child_size = max(80, int(settings.rag_chunk_size or 300))
    child_overlap = max(0, int(settings.rag_chunk_overlap or 50))

    # ---------- 1. 按标题切, 得到天然父块候选 ----------
    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=_HEADERS_TO_SPLIT_ON,
        strip_headers=False,  # 保留标题, RAG 引用更直观
    )
    header_chunks = md_splitter.split_text(content)
    if not header_chunks:
        # 文档无标题 → 整篇作为一个父块候选
        header_chunks = [Document(page_content=content, metadata={})]

    # ---------- 2. 父块超长则二次切 (结构保护) ----------
    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size=parent_max,
        chunk_overlap=0,  # 父块间无 overlap (避免父级内容重复存)
        separators=["\n\n", "\n", "。", "!", "?", "；", ";", " ", ""],
    )

    parents: list[Document] = []
    for hc in header_chunks:
        if len(hc.page_content) <= parent_max:
            parents.append(hc)
        else:
            sub_texts = _protect_and_split(hc.page_content, parent_splitter)
            for sub in sub_texts:
                parents.append(Document(page_content=sub, metadata=dict(hc.metadata or {})))

    # ---------- 3. 每个父块切成 child 小块 (结构保护) ----------
    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size=child_size,
        chunk_overlap=child_overlap,
        separators=["\n\n", "\n", "。", "!", "?", "；", ";", " ", ""],
    )

    final: List[Document] = []
    chunk_index = 0
    for parent_doc in parents:
        parent_text = parent_doc.page_content
        meta_h = parent_doc.metadata or {}
        # 章节路径前缀: 拼到 child page_content 前面, 参与 embedding
        chapter_parts = [meta_h.get("h1"), meta_h.get("h2"), meta_h.get("h3")]
        chapter = " / ".join(p for p in chapter_parts if p)
        prefix = f"[{chapter}]\n" if chapter else ""
        pid = _parent_id(parent_text)

        child_texts = _protect_and_split(parent_text, child_splitter)
        for ct in child_texts:
            if not ct.strip():
                continue
            child = Document(
                page_content=f"{prefix}{ct}",
                metadata={
                    **meta_h,
                    "source": source,
                    "chapter": chapter,
                    "parent_id": pid,
                    "parent_content": parent_text,
                    "chunk_index": chunk_index,
                },
            )
            final.append(child)
            chunk_index += 1

    logger.info(
        f"[splitter] {source}: sections={len(header_chunks)} parents={len(parents)} children={len(final)}"
    )
    return final
