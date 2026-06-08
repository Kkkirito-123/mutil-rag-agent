"""Embedding 服务.

支持两种向量化后端:
  - dashscope: 默认, 使用 text-embedding-v4
  - ollama: 本地 Ollama, 推荐 bge-m3

两种后端都实现 LangChain Embeddings 接口, 所以上层 Milvus/RAG 逻辑不用改。
切换 embedding 模型后必须重建 Milvus collection, 不能混用旧向量。
"""

from functools import lru_cache
from typing import List

import httpx
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from loguru import logger

from app.config import settings
from app.exceptions import EmbeddingError


class OllamaEmbeddings(Embeddings):
    """LangChain Embeddings adapter for Ollama `/api/embed`."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        batch_size: int,
        timeout_sec: float,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.batch_size = max(1, batch_size)
        self.timeout_sec = max(1.0, timeout_sec)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts using Ollama."""
        if not texts:
            return []

        vectors: List[List[float]] = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            vectors.extend(self._embed_batch(batch))
        return vectors

    def embed_query(self, text: str) -> List[float]:
        """Embed one query text."""
        vectors = self.embed_documents([text])
        if not vectors:
            raise EmbeddingError("Ollama embedding 返回空向量")
        return vectors[0]

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        url = f"{self.base_url}/api/embed"
        payload = {"model": self.model, "input": texts}
        try:
            with httpx.Client(timeout=self.timeout_sec) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500] if exc.response is not None else ""
            raise EmbeddingError(
                f"Ollama embedding HTTP {exc.response.status_code}: {detail}"
            ) from exc
        except Exception as exc:
            raise EmbeddingError(
                f"Ollama embedding 调用失败: {type(exc).__name__}: {exc}"
            ) from exc

        embeddings = data.get("embeddings")
        if not isinstance(embeddings, list) or not embeddings:
            raise EmbeddingError(f"Ollama embedding 响应缺少 embeddings 字段: {data}")
        if len(embeddings) != len(texts):
            raise EmbeddingError(
                f"Ollama embedding 数量不匹配: input={len(texts)}, output={len(embeddings)}"
            )
        return [[float(x) for x in vector] for vector in embeddings]


@lru_cache(maxsize=1)
def get_embeddings() -> Embeddings:
    """获取 Embedding 实例 (单例).

    Returns:
        Embeddings: LangChain Embeddings 接口的实例

    Raises:
        EmbeddingError: 如果配置不完整无法创建
    """
    provider = settings.embedding_provider
    if provider == "ollama":
        logger.info(
            f"创建 Ollama Embedding 客户端: model={settings.ollama_embedding_model}, "
            f"dim={settings.ollama_embedding_dim}, base_url={settings.ollama_base_url}"
        )
        return OllamaEmbeddings(
            base_url=settings.ollama_base_url,
            model=settings.ollama_embedding_model,
            batch_size=settings.ollama_embedding_batch_size,
            timeout_sec=settings.ollama_embedding_timeout_sec,
        )

    if not settings.dashscope_api_key:
        raise EmbeddingError("DASHSCOPE_API_KEY 未配置, 无法创建 Embedding 客户端")

    logger.info(
        f"创建 Embedding 客户端: model={settings.dashscope_embedding_model}, "
        f"dim={settings.dashscope_embedding_dim}"
    )

    return OpenAIEmbeddings(
        model=settings.dashscope_embedding_model,
        api_key=settings.dashscope_api_key,  # type: ignore[arg-type]
        base_url=settings.dashscope_base_url,
        dimensions=settings.dashscope_embedding_dim,
        check_embedding_ctx_length=False,  # DashScope 无 tiktoken, 关掉检查
        # DashScope text-embedding-v4 单次最多 10 个文本, 超过会 400.
        # OpenAIEmbeddings 默认 chunk_size=2048 会把所有文本一次发出去, 必须降到 10.
        chunk_size=10,
    )
