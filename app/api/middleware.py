"""API 中间件.

- RequestIDMiddleware: 为每个请求生成 UUID, 注入 logger context, 便于全链路追踪
- LoggingMiddleware  : 记录请求/响应日志 (含耗时)
"""

import time
import uuid
from typing import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """为每个请求注入 X-Request-ID.

    - 如果客户端传了 X-Request-ID 头, 复用之 (用于跨服务追踪)
    - 否则生成新的 UUID
    - 通过 contextvars 注入 Loguru 的 extra, 后续所有 logger 调用都会带上 request_id
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]

        # 把 request_id 挂到 request.state, 路由里可以直接用
        request.state.request_id = request_id

        # 注入到 loguru context (覆盖默认值 "-")
        with logger.contextualize(request_id=request_id):
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """记录每次请求的方法、路径、状态码、耗时."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = time.perf_counter()
        method = request.method
        path = request.url.path

        # 跳过静态资源和健康检查的访问日志, 避免刷屏
        skip_log = path.startswith("/static") or path.endswith("/health")

        try:
            response = await call_next(request)
            elapsed_ms = (time.perf_counter() - start) * 1000
            if not skip_log:
                logger.info(
                    f"{method} {path} -> {response.status_code} ({elapsed_ms:.1f}ms)"
                )
            return response
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                f"{method} {path} -> EXCEPTION ({elapsed_ms:.1f}ms): {e}"
            )
            raise


def setup_middlewares(app: FastAPI) -> None:
    """注册所有中间件.

    注意中间件的添加顺序: 后添加的先执行 (洋葱模型).
    所以这里先加 CORS (最外层), 最后加 RequestID (最内层).
    """
    # 日志中间件 (最内层, 拿到的是真实业务执行时间)
    app.add_middleware(LoggingMiddleware)

    # RequestID 中间件 (在日志之外)
    app.add_middleware(RequestIDMiddleware)

    # CORS (最外层)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 开发环境放开, 生产环境应限定具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
