"""LangChain VectorStore 封装 + 高级检索流水线.

为什么需要这一层?
  - core/milvus.py 提供底层连接 (pymilvus 直接用)
  - 本模块用 langchain_milvus.Milvus 包一层, 提供 LangChain 标准 VectorStore 接口
  - 这样可以无缝接入 LangChain 的 Retriever / RAG Chain 等高层能力

设计要点:
  - 单例 (lru_cache): 整个进程一份, 避免重复连接
  - 自动建库: 第一次插入数据时, langchain_milvus 会自动创建 collection
  - 维度自动: 由 Embedding 模型决定 (1024, 来自 text-embedding-v4)

高级检索流水线 (advanced_search)
  用户 query → Vector top-N → [Hybrid 融合 BM25 top-N] → [Reranker top-K] → 返回
  每一层都可通过 settings 开关; 任一环节失败都自动降级到上一层结果.
"""

from functools import lru_cache
from typing import Any, List, Optional

from langchain_core.documents import Document
from langchain_milvus import Milvus
from loguru import logger
from pymilvus import MilvusClient, connections

from app.config import settings
from app.core.embedding import get_embeddings


@lru_cache(maxsize=1)
def get_vector_store() -> Milvus:
    """获取 LangChain Milvus VectorStore 单例.

    Returns:
        Milvus: 实现了 VectorStore 接口的实例

    Notes:
        - langchain_milvus 0.3+ 用 MilvusClient (新 API),
          但底层 _extract_fields() 又用了 pymilvus.orm.Collection (旧 API).
          这两个 API 用不同的连接注册表, 导致 ConnectionNotExistException.
        - 修复: 先用 MilvusClient 拿到自动生成的 alias, 再用 connections.connect()
          把同一个 alias 注册到 ORM registry, 让两套 API 共享连接.
        - 必须用 uri 而非 host+port (MilvusClient 的强制要求)
    """
    uri = f"http://{settings.milvus_host}:{settings.milvus_port}"

    # 先创建 MilvusClient, 拿到内部 alias (形如 "cm-xxxxxx")
    probe_client = MilvusClient(uri=uri)
    internal_alias = probe_client._using

    # 把同一 alias 注册到 ORM connections registry
    # (pymilvus.orm.Collection 会从这里查 connection)
    if internal_alias not in [c[0] for c in connections.list_connections()]:
        connections.connect(alias=internal_alias, uri=uri)

    logger.info(
        f"创建 VectorStore: collection={settings.milvus_collection}, "
        f"uri={uri}, alias={internal_alias}"
    )

    return Milvus(
        embedding_function=get_embeddings(),
        collection_name=settings.milvus_collection,
        connection_args={"uri": uri},
        # 字段名约定 (与原 OnCall 项目保持一致, 方便迁移数据)
        primary_field="pk",
        text_field="content",
        vector_field="vector",
        # 索引参数: HNSW + COSINE (本地 Milvus standalone 优先稳定)。
        index_params={
            "metric_type": "COSINE",
            "index_type": "HNSW",
            "params": {"M": 8, "efConstruction": 64},
        },
        search_params={
            "metric_type": "COSINE",
            "params": {"ef": max(32, int(settings.milvus_hnsw_search_ef or 128))},
        },
        # 不存在则自动建表 (开发期友好)
        auto_id=True,
        drop_old=False,  # 不删旧数据
    )


def safe_similarity_search(
    query: str,
    k: Optional[int] = None,
    filter: Optional[str] = None,
) -> List[Document]:
    """纯向量检索, 对 collection 不存在等异常做兜底 (向后兼容入口).

    业务侧 (knowledge_tool) 直接调本函数, 不用关心 collection 是否就绪.
    若需要 Hybrid + Rerank 高级流水线, 请用 advanced_search.

    Args:
        query: 查询文本
        k: 返回 top-k (None 用 settings.rag_top_k)
        filter: Milvus 过滤表达式, 例如 "metadata['source'] == 'oncall.md'"

    Returns:
        List[Document]: 匹配的文档列表; collection 不存在或查询失败返回 []
    """
    k = k or settings.rag_top_k
    try:
        store = get_vector_store()
        kwargs: dict[str, Any] = {"k": k}
        if filter:
            kwargs["expr"] = filter
        return store.similarity_search(query, **kwargs)
    except Exception as e:
        # collection 不存在 / Milvus 暂时不可用 / 维度不匹配 等
        logger.warning(f"similarity_search 失败 (返回空): {type(e).__name__}: {e}")
        return []


async def advanced_search(
    query: str,
    k: Optional[int] = None,
    *,
    filter: Optional[str] = None,
    retrieve_k: Optional[int] = None,
    use_hybrid: Optional[bool] = None,
    use_rerank: Optional[bool] = None,
) -> List[Document]:
    """高级检索流水线: Vector → [Hybrid] → [Rerank] → 返回 top-k.

    为什么有这个函数?
      - safe_similarity_search 是"只做向量"的最小接口, 保持向后兼容
      - advanced_search 叠加 Hybrid 和 Rerank, 默认行为由 settings 控制
      - 业务层 (rag_service) 无需知道下游细节, 开关都在 config

    流水线:
      1) 向量检索粗排:     top = rag_retrieve_k (比如 20)
      2) Hybrid 融合:      与 BM25 的 top-20 RRF 融合, 取前 rag_retrieve_k
      3) Rerank 精排:      交给 reranker 取 top-k (默认 3)
      任一环节故障都自动降级到上一层结果.

    Args:
        query:       查询文本
        k:           最终返回的 top-k (None = settings.rag_top_k)
        filter:      Milvus 过滤表达式, 透传给向量检索
        retrieve_k:  送入 hybrid/rerank 前的候选数 (None = settings.rag_retrieve_k)
        use_hybrid:  是否做 Hybrid (None = settings.rag_hybrid_enabled)
        use_rerank:  是否做 Rerank (None = settings.rag_rerank_enabled)

    Returns:
        List[Document]: 最终 top-k, 不抛异常.
    """
    # 延迟导入避免循环依赖
    from app.core.hybrid_retriever import _bm25_index, hybrid_search, refresh_bm25_index
    from app.core.reranker import rerank_docs

    final_k = k or settings.rag_top_k
    use_hybrid = settings.rag_hybrid_enabled if use_hybrid is None else use_hybrid
    use_rerank = settings.rag_rerank_enabled if use_rerank is None else use_rerank

    # 送进 reranker 前的候选数 (Hybrid / Vector 都取这么多)
    if use_hybrid or use_rerank:
        retrieve_k = max(final_k, retrieve_k or settings.rag_retrieve_k)
    else:
        retrieve_k = final_k

    # ---------- Step 1: 向量粗排 ----------
    vector_docs = safe_similarity_search(query, k=retrieve_k, filter=filter)
    if not vector_docs:
        return []

    # ---------- Step 2: Hybrid 融合 ----------
    candidates = vector_docs
    if use_hybrid:
        # 首次调用时惰性构建 BM25 索引 (从 Milvus 拉全量)
        if not _bm25_index.is_ready:
            try:
                refresh_bm25_index()
            except Exception as e:
                logger.warning(f"[advanced_search] BM25 lazy build 失败: {type(e).__name__}: {e}")
        candidates = hybrid_search(query, vector_docs, k=retrieve_k, retrieve_k=retrieve_k)

    # ---------- Step 3: Rerank 精排 ----------
    if use_rerank and len(candidates) > final_k:
        try:
            candidates = await rerank_docs(query, candidates, top_n=final_k)
        except Exception as e:
            # rerank_docs 内部已有兜底, 这里只是二次保险
            logger.warning(f"[advanced_search] rerank 异常兜底: {type(e).__name__}: {e}")
            candidates = candidates[:final_k]
    else:
        candidates = candidates[:final_k]

    return candidates
