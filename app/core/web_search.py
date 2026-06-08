"""联网搜索 Provider + 结果格式化 (单一实现).

调用方:
  - app.services.rag_service: 走结构化 hits, 自己拼提示
  - mcp_servers.websearch_server: 加黑名单/脱敏/限频后转 Markdown 返回给 Agent
"""

from __future__ import annotations

import os
from typing import Any, Dict, List


def get_provider() -> str:
    """从 settings (优先) 或环境变量解析 provider 名."""
    try:
        from app.config import settings
        val = settings.web_search_provider
    except Exception:
        val = os.environ.get("WEB_SEARCH_PROVIDER", "")
    provider = (val or "mock").lower().strip()
    if provider == "tavily":
        return "open_websearch"
    return provider


def get_open_websearch_config() -> dict[str, Any]:
    try:
        from app.config import settings
        return {
            "base_url": (settings.open_websearch_base_url or "").strip(),
            "engine": (settings.open_websearch_engine or "").strip(),
            "search_mode": (settings.open_websearch_search_mode or "").strip(),
            "timeout": float(settings.open_websearch_timeout_sec or 15.0),
        }
    except Exception:
        return {
            "base_url": (os.environ.get("OPEN_WEBSEARCH_BASE_URL") or "http://127.0.0.1:3210").strip(),
            "engine": (os.environ.get("OPEN_WEBSEARCH_ENGINE") or "bing").strip(),
            "search_mode": (os.environ.get("OPEN_WEBSEARCH_SEARCH_MODE") or "auto").strip(),
            "timeout": float(os.environ.get("OPEN_WEBSEARCH_TIMEOUT_SEC") or 15.0),
        }


def search_open_websearch(query: str, max_results: int) -> List[Dict[str, Any]]:
    """open-webSearch local daemon provider. 默认地址: http://127.0.0.1:3210."""
    import httpx

    cfg = get_open_websearch_config()
    base_url = str(cfg["base_url"]).rstrip("/")
    if not base_url:
        raise RuntimeError("OPEN_WEBSEARCH_BASE_URL 未配置")

    payload: dict[str, Any] = {
        "query": query,
        "limit": max_results,
    }
    engine = str(cfg.get("engine") or "").strip()
    if engine:
        payload["engines"] = [engine]
    search_mode = str(cfg.get("search_mode") or "").strip()
    if search_mode and search_mode != "auto":
        payload["searchMode"] = search_mode

    resp = httpx.post(
        f"{base_url}/search",
        json=payload,
        timeout=float(cfg.get("timeout") or 15.0),
    )
    resp.raise_for_status()
    envelope = resp.json()
    if envelope.get("status") != "ok":
        err = envelope.get("error") or {}
        message = err.get("message") if isinstance(err, dict) else str(err)
        raise RuntimeError(message or "open-webSearch 返回 error")

    data = envelope.get("data") or {}
    return [
        {
            "title": r.get("title", "(无标题)"),
            "url": r.get("url", ""),
            "snippet": r.get("description") or r.get("snippet") or r.get("content", ""),
            "engine": r.get("engine", ""),
            "source": r.get("source", ""),
        }
        for r in data.get("results", [])
        if isinstance(r, dict)
    ]


def search_ddgs(query: str, max_results: int) -> List[Dict[str, Any]]:
    """DuckDuckGo (零配置, 国内访问不稳, 需 pip install ddgs)."""
    try:
        from ddgs import DDGS  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "ddgs 未安装. 运行 `pip install ddgs`, 或切换 WEB_SEARCH_PROVIDER=mock"
        ) from e

    with DDGS() as client:
        return [
            {
                "title": r.get("title", "(无标题)"),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in client.text(query, max_results=max_results)
        ]


def search_mock(query: str, max_results: int) -> List[Dict[str, Any]]:
    """Mock provider (默认无外部依赖, 内容标注 [MOCK])."""
    return [
        {
            "title": f"[MOCK] 关于 '{query}' 的搜索示例",
            "url": "https://example.com/mock-search-result",
            "snippet": (
                f"这是 web_search 的 Mock 占位返回 (provider=mock). "
                f"启动 open-webSearch daemon 并配置 WEB_SEARCH_PROVIDER=open_websearch 可使用真实搜索. "
                f"原始查询: {query!r}. "
                f"Mock 模式下不要把结果当真实信源引用."
            ),
        }
    ]


def search(query: str, max_results: int, provider: str | None = None) -> List[Dict[str, Any]]:
    """按 provider 调度. 调用方负责异常处理."""
    p = (provider or get_provider()).lower().strip()
    if p == "tavily":
        p = "open_websearch"
    if p in {"open_websearch", "open-websearch", "openwebsearch"}:
        return search_open_websearch(query, max_results)
    if p == "ddgs":
        return search_ddgs(query, max_results)
    if p == "mock":
        return search_mock(query, max_results)
    raise ValueError(f"未知 web_search provider: {p!r} (可选 open_websearch / mock / ddgs)")


def format_results(results: List[Dict[str, Any]], *, provider: str) -> str:
    """把搜索结果格式化为 Markdown."""
    header = ""
    if provider == "mock":
        header = (
            "> **[WARN] provider=mock**: 以下结果为占位数据, 仅供演示, "
            "不要在最终报告中作为真实信源引用.\n\n"
        )
    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title") or "(无标题)"
        url = r.get("url") or "(无 URL)"
        snippet = (r.get("snippet") or "").strip()
        lines.append(f"### {i}. {title}\n来源: {url}\n\n{snippet}")
    return header + "\n\n---\n\n".join(lines)
