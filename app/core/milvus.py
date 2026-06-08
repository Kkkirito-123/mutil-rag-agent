"""Milvus 客户端管理.

职责划分:
  - 本模块: 底层连接管理 + 健康检查 + Collection 元数据管理
  - services/vector_store.py (后续阶段): 高层向量操作 (用 langchain_milvus.Milvus 包装)

为什么分两层?
  - 底层用 pymilvus, 提供精细控制 (健康检查、维度校验、强制重建)
  - 高层用 langchain_milvus, 与 LangChain 生态无缝衔接 (RAG / Retriever)
"""

from typing import List, Optional

from loguru import logger
from pymilvus import MilvusException, connections, utility

from app.config import settings
from app.exceptions import VectorStoreError


class MilvusManager:
    """Milvus 连接管理器 (单例).

    通过 lifespan 钩子在应用启动时 connect(), 关闭时 disconnect().

    Examples:
        # main.py lifespan
        milvus_manager.connect()
        ...
        milvus_manager.disconnect()

        # health check
        if not milvus_manager.is_alive():
            raise ServiceError("Milvus down")
    """

    DEFAULT_ALIAS = "default"

    def __init__(self) -> None:
        self._connected = False

    # ==================== 连接管理 ====================

    def connect(self) -> None:
        """建立 Milvus 连接 (幂等)."""
        if self._connected:
            logger.debug("Milvus 已连接, 跳过")
            return

        host = settings.milvus_host
        port = settings.milvus_port
        timeout = settings.milvus_timeout_ms / 1000

        logger.info(f"连接 Milvus: {host}:{port} (timeout={timeout}s)")
        try:
            connections.connect(
                alias=self.DEFAULT_ALIAS,
                host=host,
                port=str(port),
                timeout=timeout,
            )
            self._connected = True
            logger.info(f"Milvus 连接成功 | 已有 collections: {self.list_collections()}")
        except MilvusException as e:
            self._connected = False
            raise VectorStoreError(
                f"Milvus 连接失败 ({host}:{port}): {e}",
                detail={"host": host, "port": port},
            ) from e
        except Exception as e:
            self._connected = False
            raise VectorStoreError(
                f"Milvus 连接异常: {e}",
                detail={"host": host, "port": port},
            ) from e

    def disconnect(self) -> None:
        """断开连接 (幂等)."""
        if not self._connected:
            return
        try:
            connections.disconnect(self.DEFAULT_ALIAS)
            logger.info("Milvus 连接已断开")
        except Exception as e:
            logger.warning(f"断开 Milvus 失败 (忽略): {e}")
        finally:
            self._connected = False

    # ==================== 健康检查 ====================

    def is_alive(self) -> bool:
        """快速健康检查 (用于 readiness probe).

        Returns:
            bool: True = 连接活跃, False = 不可用
        """
        if not self._connected:
            return False
        try:
            # 试着获取连接地址, 失败说明连接已掉
            addr = connections.get_connection_addr(self.DEFAULT_ALIAS)
            return bool(addr)
        except Exception as e:
            logger.warning(f"Milvus health check 失败: {e}")
            return False

    @property
    def is_connected(self) -> bool:
        return self._connected

    # ==================== Collection 管理 ====================

    def list_collections(self) -> List[str]:
        """列出所有 collection."""
        if not self._connected:
            return []
        try:
            return utility.list_collections(using=self.DEFAULT_ALIAS)
        except Exception as e:
            logger.warning(f"list_collections 失败: {e}")
            return []

    def has_collection(self, name: Optional[str] = None) -> bool:
        """检查 collection 是否存在."""
        col = name or settings.milvus_collection
        try:
            return utility.has_collection(collection_name=col, using=self.DEFAULT_ALIAS)
        except Exception as e:
            logger.warning(f"has_collection({col}) 失败: {e}")
            return False

    def drop_collection(self, name: Optional[str] = None) -> None:
        """删除 collection (危险操作!).

        会同时删除所有数据和索引, 不可恢复.
        通常仅在维度变更或开发期重置时使用.
        """
        col = name or settings.milvus_collection
        try:
            utility.drop_collection(col, using=self.DEFAULT_ALIAS)
            logger.warning(f"已删除 collection: {col}")
        except Exception as e:
            raise VectorStoreError(f"删除 collection 失败: {e}") from e


# ============================================================
# 全局单例
# ============================================================
milvus_manager = MilvusManager()
