"""知识库检索: Parent-Child RAG。

中性原语层 (app/rag/): 只依赖 config + core.vector_store。tools/knowledge_tool 和
services/rag_service 都从这里取, 避免 tools 反向 import services 的反向依赖。

Parent-Child 流程:
  1. advanced_search 在 Milvus 上找最相似的 child 小块 (top_k 多取一些, 给去重留余量)
  2. 按 parent_id 去重: 同一个 parent 下多个 child 命中, 只算一次 (取最高分)
  3. 用 parent_content 拼 context 返回 (而不是 child page_content) → LLM 拿到完整段落

为什么这么做: child 小利于 embedding 命中, parent 大利于 LLM 推理。
参考腾讯 WeKnora 的 parent-child chunking 设计 (app/utils/splitter.py)。
"""

from typing import Any

from app.config import settings
from app.core.vector_store import advanced_search


# Milvus 召回时多取一些 child, 给 parent_id 去重留余量 (经验值 3 倍)
_CHILD_OVERFETCH = 3


async def build_context(
    question: str,
    top_k: int | None = None,
) -> tuple[str, int, list[str], list[dict[str, Any]]]:
    """检索知识库, 拼接成 context 字符串 (Parent-Child)。

    Returns:
        (context_text, parent_hit_count, sources, hits_meta)
        hits_meta: [{"source", "chapter", "preview", "score", "parent_id"}, ...]
    """
    final_k = max(1, int(top_k or settings.rag_top_k))
    parent_max = max(500, int(settings.rag_parent_max_chars or 2400))

    # 多拉一些 child, 再按 parent 去重
    docs = await advanced_search(
        question,
        k=final_k * _CHILD_OVERFETCH,
        use_hybrid=settings.rag_hybrid_enabled,
        use_rerank=settings.rag_rerank_enabled,
    )
    if not docs:
        return "(知识库未命中相关内容)", 0, [], []

    # ---------- 按 parent_id 去重 ----------
    # 同一个 parent 下多个 child 命中, 只保留首次 (advanced_search 已按相关性排序);
    # 没有 parent_id 的旧索引数据降级为按 page_content 去重 (向后兼容)。
    seen_parents: set[str] = set()
    unique_parents: list[dict[str, Any]] = []
    for doc in docs:
        meta = doc.metadata or {}
        pid = str(meta.get("parent_id") or "")
        key = pid or f"__legacy:{hash(doc.page_content)}"
        if key in seen_parents:
            continue
        seen_parents.add(key)
        parent_text = str(meta.get("parent_content") or doc.page_content)
        unique_parents.append({"doc": doc, "parent_text": parent_text, "key": key})
        if len(unique_parents) >= final_k:
            break

    # ---------- 拼 context ----------
    chunks: list[str] = []
    sources: list[str] = []
    hits_meta: list[dict[str, Any]] = []
    for i, item in enumerate(unique_parents, 1):
        doc = item["doc"]
        meta = doc.metadata or {}
        source = meta.get("source") or "未知"
        sources.append(str(source))
        chapter = meta.get("chapter") or ""
        header = f"## 来源 {i} | {source}"
        if chapter:
            header += f" | 章节: {chapter}"
        parent_text = item["parent_text"].strip()
        truncated = parent_text[:parent_max]
        if len(parent_text) > parent_max:
            truncated += "... (已截断)"
        chunks.append(f"{header}\n{truncated}")

        score = meta.get("score") or meta.get("rerank_score") or meta.get("distance")
        try:
            score_val = round(float(score), 4) if score is not None else None
        except Exception:
            score_val = None
        # preview 用 child page_content (小块, 更精准展示"命中片段")
        preview = doc.page_content.replace("\n", " ")
        hits_meta.append(
            {
                "source": str(source),
                "chapter": str(chapter) if chapter else "",
                "preview": preview[:240] + ("..." if len(preview) > 240 else ""),
                "score": score_val,
                "parent_id": str(meta.get("parent_id") or ""),
            }
        )

    return "\n\n".join(chunks), len(unique_parents), sources, hits_meta
