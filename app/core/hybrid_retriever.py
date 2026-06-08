"""Hybrid Retriever: BM25 (稀疏) + Vector (稠密) + RRF 融合.

为什么要加 Hybrid Search
======================
纯向量检索在语义泛化上强, 但有两个典型失手场景:
  1) **精确 token 匹配丢失**: 用户输入 "ERR_CONN_REFUSED" 或 "redis.exception.TimeoutError",
     这些是固定字符串 / 错误码 / 服务名, 向量编码会把它们"揉"进语义空间, 反而不如
     BM25 这种基于词频的算法精确命中.
  2) **罕见长尾词**: 比如内部自定义的组件名 "oncall-dispatcher", 训练语料里几乎没有,
     embedding 质量差; BM25 不依赖语义, 见字如面.

Hybrid 策略: 让 BM25 (sparse) 和 Vector (dense) 各出候选, 再用 RRF 融合去重排名.
业界共识 (bswen 2026 / Anthropic / Weaviate): Hybrid 通常比单一检索 recall 高 5-15%.

为什么选 RRF (Reciprocal Rank Fusion) 而不是加权分数
======================
  - BM25 分数是无上界的 (可能 5.0, 也可能 50.0, 依赖文档长度),
    向量 cosine 是 [-1, 1], 两者量纲完全不同, 直接加权要先做归一化.
  - RRF 只用"排名"不看绝对分数: score = Σ 1/(k + rank_i), 天然融合多路,
    对量纲不敏感, 是学术和工业界默认选择 (k=60 是 TREC 经典值).

为什么中文不用 jieba 分词
======================
  - 向量检索已经覆盖了中文语义, BM25 的核心价值是"捕获向量漏掉的精确 token".
    这些 token 基本是英文 / 数字 / 错误码, 按字切 + 英文按空格切已经够用.
  - 省掉 jieba 依赖 (几 MB + 词典加载耗时), 启动更轻.
  - 局限: 纯中文长句 (比如"数据库连接池满了怎么办") 在 BM25 那一路会被打散成单字,
    recall 会略差; 但这种场景本来就是向量的强项, 整体不影响.

索引刷新
======================
  - BM25 索引是**纯内存**, 进程启动时从 Milvus 拉全量 chunks 构建
  - 文档上传/删除后, 调 refresh() 重建 (小规模毫秒级)
  - 局限: 多副本部署时每个副本都要各自构建; 大规模 (10 万 chunks+) 建议改为
    Elasticsearch / OpenSearch 托管索引
"""

from __future__ import annotations

import re
import threading
from typing import Dict, List, Optional, Tuple

from langchain_core.documents import Document
from loguru import logger

from app.config import settings

try:
    from rank_bm25 import BM25Okapi
except ImportError:  # pragma: no cover
    BM25Okapi = None  # type: ignore
    logger.warning(
        "[hybrid] rank_bm25 未安装, Hybrid Search 将自动降级到纯向量. "
        "安装: pip install rank_bm25>=0.2.2"
    )


# ---------------------------------------------------------------------------
# 分词器
# ---------------------------------------------------------------------------
# 策略: 英文/数字按空格切 + 中文按单字切
# 为什么这么写见文件 docstring; 核心: BM25 只负责精确 token, 不追求中文语义
_CJK_RE = re.compile(r"([\u4e00-\u9fff])")
_TOKEN_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_\-\.]*|[\u4e00-\u9fff]")


def _tokenize(text: str) -> List[str]:
    """轻量分词: 英文按 token 切 (保留 dot/dash/underscore), 中文按字.

    Examples:
        _tokenize("Redis 内存 98% OOM")
        -> ["redis", "内", "存", "98", "oom"]

        _tokenize("ERR_CONN_REFUSED 怎么办")
        -> ["err_conn_refused", "怎", "么", "办"]
    """
    if not text:
        return []
    tokens = _TOKEN_RE.findall(text.lower())
    # 过滤单字母/空噪声
    return [t for t in tokens if t]


# ---------------------------------------------------------------------------
# BM25 索引 (进程内单例)
# ---------------------------------------------------------------------------
class _BM25Index:
    """BM25 索引 (线程安全单例, 惰性构建).

    构建时机:
      - 第一次检索时 (lazy): 从 Milvus 拉全量 chunks 构建
      - 文档上传/删除后: document_service 调 refresh() 主动刷新
    """

    def __init__(self) -> None:
        self._bm25: Optional["BM25Okapi"] = None
        self._docs: List[Document] = []
        self._lock = threading.Lock()
        self._built = False

    def build(self, docs: List[Document]) -> None:
        """用给定文档构建 BM25.

        Args:
            docs: 所有候选文档 (通常来自 Milvus 全量拉取)
        """
        if BM25Okapi is None:
            self._built = True  # 标记已尝试, 避免反复重建
            return

        if not docs:
            logger.info("[hybrid] 文档为空, BM25 索引跳过")
            with self._lock:
                self._bm25 = None
                self._docs = []
                self._built = True
            return

        tokenized = [_tokenize(d.page_content) for d in docs]
        try:
            bm25 = BM25Okapi(tokenized)
        except Exception as e:
            logger.warning(f"[hybrid] BM25 构建失败 (降级): {type(e).__name__}: {e}")
            with self._lock:
                self._bm25 = None
                self._docs = []
                self._built = True
            return

        with self._lock:
            self._bm25 = bm25
            self._docs = docs
            self._built = True
        logger.info(f"[hybrid] BM25 索引构建完成: {len(docs)} 文档")

    def search(self, query: str, k: int) -> List[Tuple[Document, float]]:
        """BM25 检索.

        Returns:
            List[(Document, score)]: 按分数降序, 长度 <= k. BM25 不可用时返回 [].
        """
        if not self._built or self._bm25 is None or not self._docs:
            return []

        tokens = _tokenize(query)
        if not tokens:
            return []

        try:
            scores = self._bm25.get_scores(tokens)
        except Exception as e:
            logger.warning(f"[hybrid] BM25 打分失败 (降级): {type(e).__name__}: {e}")
            return []

        # 取 top-k
        # argsort 慢但 k 小 (<=50) 可接受; 需要可换 np.argpartition
        indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:k]
        return [(self._docs[i], float(s)) for i, s in indexed if s > 0]

    @property
    def is_ready(self) -> bool:
        return self._built and self._bm25 is not None


_bm25_index = _BM25Index()


# ---------------------------------------------------------------------------
# 对外接口
# ---------------------------------------------------------------------------
def refresh_bm25_index() -> None:
    """重建 BM25 索引 (从 Milvus 拉全量 chunks).

    调用时机:
      - 应用启动 lifespan (可选, 否则首次检索时 lazy 构建)
      - document_service 上传 / 删除后 (如果 rag_bm25_refresh_on_upload=True)

    失败兜底: 拉不到数据时保持上一份索引 (若有), 不阻断业务.
    """
    if BM25Okapi is None:
        logger.warning("[hybrid] rank_bm25 未安装, 跳过 refresh")
        return

    docs = _load_all_chunks_from_milvus()
    _bm25_index.build(docs)


def _load_all_chunks_from_milvus() -> List[Document]:
    """从 Milvus 拉全量 chunks (用于构建 BM25 索引).

    局限: 用 col.query(expr="pk >= 0", limit=16384). 超过 16k chunks 需分页.
    这里为 demo 简化, 生产环境建议维护独立元数据表.
    """
    try:
        from pymilvus import Collection, MilvusClient, connections

        uri = f"http://{settings.milvus_host}:{settings.milvus_port}"
        client = MilvusClient(uri=uri)
        if not client.has_collection(settings.milvus_collection):
            return []

        alias = client._using
        if alias not in [c[0] for c in connections.list_connections()]:
            connections.connect(alias=alias, uri=uri)

        col = Collection(settings.milvus_collection, using=alias)
        col.load()
        rows = col.query(
            expr="pk >= 0",
            output_fields=[
                "content",
                "source",
                "chapter",
                "parent_id",
                "parent_content",
                "chunk_index",
            ],
            limit=16384,
        )
    except Exception as e:
        logger.warning(f"[hybrid] 从 Milvus 拉全量失败 (降级): {type(e).__name__}: {e}")
        return []

    docs: List[Document] = []
    for row in rows:
        content = row.get("content") or ""
        if not content:
            continue
        meta = {
            "source": row.get("source") or "未知",
            "chapter": row.get("chapter") or "",
            "parent_id": row.get("parent_id") or "",
            "parent_content": row.get("parent_content") or "",
            "chunk_index": row.get("chunk_index"),
        }
        docs.append(Document(page_content=content, metadata=meta))
    return docs


def hybrid_search(
    query: str,
    vector_docs: List[Document],
    *,
    k: int,
    retrieve_k: Optional[int] = None,
    bm25_weight: Optional[float] = None,
) -> List[Document]:
    """将 Vector 结果和 BM25 结果用 RRF 融合, 返回 top-k.

    Args:
        query:        用户查询
        vector_docs:  向量检索已拿到的 top-N (调用方传入)
        k:            融合后返回的文档数
        retrieve_k:   BM25 侧候选数 (None = settings.rag_retrieve_k)
        bm25_weight:  BM25 路的权重 (None = settings.rag_hybrid_bm25_weight)

    Returns:
        List[Document]: 融合去重后的 top-k

    降级策略:
        - BM25 不可用 → 直接返回 vector_docs[:k]
        - vector_docs 为空 且 BM25 为空 → 返回 []
    """
    bm25_weight = bm25_weight if bm25_weight is not None else settings.rag_hybrid_bm25_weight
    vec_weight = 1.0 - bm25_weight

    # 1) BM25 那一路 (取同样的 retrieve_k, 让两路对称)
    candidate_k = max(k, retrieve_k or settings.rag_retrieve_k)
    bm25_results = _bm25_index.search(query, candidate_k) if _bm25_index.is_ready else []

    if not bm25_results:
        # BM25 不可用时直接返回纯向量 top-k
        logger.debug("[hybrid] BM25 路为空, 返回纯向量结果")
        return vector_docs[:k]

    # 2) RRF 融合
    # RRF 公式: score(d) = Σ weight_i / (rrf_k + rank_i(d))
    # rrf_k=60 是 TREC 经典默认值, 小知识库可通过 benchmark 调参。
    rrf_k = max(1, int(settings.rag_hybrid_rrf_k or 60))
    scores: Dict[str, float] = {}
    doc_map: Dict[str, Document] = {}

    def _key(doc: Document) -> str:
        """用 (source, chapter, content hash) 做唯一键, 去重."""
        meta = doc.metadata or {}
        return f"{meta.get('source', '')}|{meta.get('chapter', '')}|{hash(doc.page_content)}"

    for rank, doc in enumerate(vector_docs):
        kk = _key(doc)
        scores[kk] = scores.get(kk, 0.0) + vec_weight / (rrf_k + rank + 1)
        doc_map.setdefault(kk, doc)

    for rank, (doc, _score) in enumerate(bm25_results):
        kk = _key(doc)
        scores[kk] = scores.get(kk, 0.0) + bm25_weight / (rrf_k + rank + 1)
        doc_map.setdefault(kk, doc)

    # 3) 按融合分排序
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top = [doc_map[kk] for kk, _ in ranked[:k]]

    logger.info(
        f"[hybrid] fused: query={query[:40]!r} "
        f"vec={len(vector_docs)} bm25={len(bm25_results)} -> top={len(top)}"
    )
    return top
