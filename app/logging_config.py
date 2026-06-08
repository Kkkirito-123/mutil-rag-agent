"""日志配置.

基于 Loguru 实现:
  - 控制台输出 (彩色, 开发友好)
  - 文件输出 (按天滚动, 自动压缩, 自动清理)
  - Request ID 上下文 (全链路追踪)
  - 拦截标准 logging 模块的输出 (统一到 Loguru)

调用约定:
  应用启动时调用 setup_logging() 一次, 后续直接 from loguru import logger 使用.
"""

import logging
import sys
from pathlib import Path

from loguru import logger

from app.config import settings


def setup_logging() -> None:
    """初始化日志系统.

    必须在应用启动时调用一次.
    """
    # 清掉默认 handler (避免重复输出)
    logger.remove()

    # ---------- 控制台 ----------
    # 开发模式用彩色, 生产模式用 JSON 格式 (便于日志聚合)
    if settings.debug:
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{extra[request_id]}</cyan> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    else:
        console_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
            "{extra[request_id]} | {name}:{function}:{line} | {message}"
        )

    logger.add(
        sys.stdout,
        level=settings.log_level,
        format=console_format,
        colorize=settings.debug,
        backtrace=True,
        diagnose=settings.debug,  # 生产环境关闭, 避免泄露敏感变量
    )

    # ---------- 文件 ----------
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        level=settings.log_level,
        rotation="00:00",  # 每天午夜滚动
        retention=f"{settings.log_retention_days} days",
        compression="zip",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
            "{extra[request_id]} | {name}:{function}:{line} | {message}"
        ),
        encoding="utf-8",
        enqueue=True,  # 异步写入, 不阻塞主线程
        backtrace=True,
        diagnose=False,
    )

    # 给 logger 的 extra 设默认值, 避免 KeyError
    logger.configure(extra={"request_id": "-"})

    # ---------- 拦截标准 logging ----------
    # uvicorn / fastapi / pymilvus 等用的是标准 logging, 拦截后统一用 loguru
    _intercept_std_logging()

    logger.info(
        f"日志系统已初始化 | level={settings.log_level} | "
        f"dir={log_dir.absolute()} | debug={settings.debug}"
    )


class _InterceptHandler(logging.Handler):
    """拦截标准 logging 模块的输出, 转发给 Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        # 找出对应的 Loguru 级别
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 找出真正的调用者 (跳过 logging 框架自身的栈帧)
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def _intercept_std_logging() -> None:
    """让标准 logging 调用都走 Loguru."""
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)

    # 调整一些第三方库的日志级别 (避免太嘈杂)
    for noisy in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
