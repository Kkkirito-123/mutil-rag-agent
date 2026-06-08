"""自定义异常.

设计原则:
  - 所有业务异常继承 AppException
  - 每个异常带 status_code (HTTP 状态码) 和 code (业务错误码)
  - 中间件 / 全局异常处理器据此返回统一的 ApiResponse
"""

from typing import Any, Optional


class AppException(Exception):
    """应用基础异常.

    所有业务异常都应继承此类.
    """

    status_code: int = 500
    code: str = "INTERNAL_ERROR"
    message: str = "服务内部错误"

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
        detail: Optional[Any] = None,
    ) -> None:
        self.message = message or self.message
        self.code = code or self.code
        self.status_code = status_code or self.status_code
        self.detail = detail
        super().__init__(self.message)

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "detail": self.detail,
        }


# ==================== 4xx 客户端错误 ====================


class BadRequestError(AppException):
    """请求参数错误."""

    status_code = 400
    code = "BAD_REQUEST"
    message = "请求参数错误"


class NotFoundError(AppException):
    """资源不存在."""

    status_code = 404
    code = "NOT_FOUND"
    message = "资源不存在"


class DocumentNotFoundError(NotFoundError):
    """文档不存在."""

    code = "DOCUMENT_NOT_FOUND"
    message = "文档不存在"


class UnsupportedFileTypeError(BadRequestError):
    """不支持的文件类型."""

    code = "UNSUPPORTED_FILE_TYPE"
    message = "不支持的文件类型, 仅支持 .md / .txt"


# ==================== 5xx 服务端错误 ====================


class ServiceError(AppException):
    """业务服务错误."""

    status_code = 500
    code = "SERVICE_ERROR"
    message = "服务执行失败"


class VectorStoreError(ServiceError):
    """向量数据库操作错误."""

    code = "VECTOR_STORE_ERROR"
    message = "向量数据库操作失败"


class EmbeddingError(ServiceError):
    """向量化错误."""

    code = "EMBEDDING_ERROR"
    message = "文本向量化失败"


class LLMError(ServiceError):
    """LLM 调用错误."""

    code = "LLM_ERROR"
    message = "大模型调用失败"


class MCPConnectionError(ServiceError):
    """MCP 服务连接错误."""

    status_code = 503
    code = "MCP_CONNECTION_ERROR"
    message = "MCP 服务不可用"


class AgentExecutionError(ServiceError):
    """Agent 执行错误."""

    code = "AGENT_EXECUTION_ERROR"
    message = "智能体执行失败"
