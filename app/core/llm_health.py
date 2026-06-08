"""LLM 健康探测.

用于在 DashScope (云端 Qwen) 不可达时, 自动切换到本地 LLM (Ollama).

设计要点:
  - **TCP 层探测**, 不发真实 API 调用, 不消耗 token, 不计费
  - 探测结果缓存 N 秒 (默认 30s), 避免每次 LLM 调用都探测
  - 线程安全 (Lock)
  - 异常友好: 任何异常都视为不可达
"""

from __future__ import annotations

import socket
import time
from threading import Lock
from urllib.parse import urlparse

from loguru import logger

from app.config import settings

_lock = Lock()
_last_probe_time: float = 0.0
_last_probe_result: bool = True  # 首次假设可用, 第一次实际调用时探测


def _extract_host_port(base_url: str, default_port: int = 443) -> tuple[str, int]:
    """从 base_url 抽取 host 和 port. 解析失败时回退 settings.local_llm_probe_host:443."""
    try:
        parsed = urlparse(base_url)
        host = parsed.hostname or settings.local_llm_probe_host
        port = parsed.port or (443 if parsed.scheme == "https" else default_port)
        return host, port
    except Exception:
        return settings.local_llm_probe_host, default_port


def _do_probe(host: str, port: int, timeout: float = 3.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, socket.gaierror, ConnectionRefusedError, OSError) as e:
        logger.debug(f"[LLMHealth] {host}:{port} 不可达: {e}")
        return False
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[LLMHealth] 探测异常: {e}")
        return False


def is_primary_llm_available(force_refresh: bool = False) -> bool:
    """检查 DashScope (主 LLM) 是否可达.

    Args:
        force_refresh: 是否强制重新探测 (忽略缓存)
    Returns:
        True = 可达, False = 不可达 (建议切到本地 LLM)
    """
    global _last_probe_time, _last_probe_result

    now = time.time()
    ttl = max(5, settings.local_llm_probe_ttl_sec)

    if not force_refresh and now - _last_probe_time < ttl:
        return _last_probe_result

    with _lock:
        # 双重检查 (其它线程可能已经更新过)
        if not force_refresh and now - _last_probe_time < ttl:
            return _last_probe_result

        host, port = _extract_host_port(settings.dashscope_base_url)
        result = _do_probe(host, port)
        # 状态变化时打 INFO, 否则 DEBUG (避免日志刷屏)
        if result != _last_probe_result:
            if result:
                logger.info(f"[LLMHealth] 主 LLM 已恢复可达: {host}:{port}")
            else:
                logger.warning(
                    f"[LLMHealth] 主 LLM 不可达: {host}:{port}, "
                    f"将回退到本地 LLM ({settings.local_llm_base_url} / "
                    f"{settings.local_llm_model})"
                )
        _last_probe_result = result
        _last_probe_time = now

    return _last_probe_result


def is_local_llm_available() -> bool:
    """探测本地 LLM (Ollama) 是否可达."""
    host, port = _extract_host_port(
        settings.local_llm_base_url, default_port=11434
    )
    return _do_probe(host, port, timeout=2.0)


def reset_probe_cache() -> None:
    """清空探测缓存, 下次调用 is_primary_llm_available() 会强制重新探测.

    主要用于测试.
    """
    global _last_probe_time, _last_probe_result
    with _lock:
        _last_probe_time = 0.0
        _last_probe_result = True
