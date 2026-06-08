"""通用响应模型.

所有接口都用 ApiResponse 包装, 返回结构统一:
{
  "code": "SUCCESS" | "ERROR_CODE",
  "message": "描述",
  "data": <实际数据> | null,
  "request_id": "uuid" (由中间件注入)
}
"""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """错误详情."""

    code: str = Field(..., description="错误代码 (业务码)")
    message: str = Field(..., description="错误消息 (用户可读)")
    detail: Optional[Any] = Field(None, description="错误详情 (调试用)")


class ApiResponse(BaseModel, Generic[T]):
    """统一响应格式.

    使用泛型支持任意 data 类型. 例:
        ApiResponse[ChatData]
        ApiResponse[list[Document]]
    """

    code: str = Field(default="SUCCESS", description="响应代码")
    message: str = Field(default="ok", description="响应消息")
    data: Optional[T] = Field(default=None, description="数据载荷")
    request_id: Optional[str] = Field(default=None, description="请求 ID (链路追踪)")

    @classmethod
    def success(cls, data: Optional[T] = None, message: str = "ok") -> "ApiResponse[T]":
        return cls(code="SUCCESS", message=message, data=data)

    @classmethod
    def error(
        cls,
        code: str,
        message: str,
        detail: Optional[Any] = None,
    ) -> "ApiResponse[ErrorDetail]":
        return cls(
            code=code,
            message=message,
            data=ErrorDetail(code=code, message=message, detail=detail),  # type: ignore
        )
