"""WebSearch MCP server.

仅做硬约束 (黑名单 / 脱敏 / 限频), provider 实现复用 app.core.web_search.
独立进程, 通过 streamable-http 暴露给主应用.
"""

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from fastmcp import FastMCP
from loguru import logger

# 让独立进程也能 import app.core.web_search
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv()

from app.core.web_search import format_results, get_provider, search  # noqa: E402

mcp = FastMCP(name="WebSearchServer")


# ============================================================
# 硬约束: 黑名单 / 限频 / 脱敏
# ============================================================
_BLOCKED_KEYWORDS = (
    "动漫", "漫画", "电影", "电视剧", "番剧", "小说", "二次元",
    "游戏", "刀剑神域", "原神", "崩坏",
    "天气", "旅游", "美食", "菜谱", "星座", "八卦",
    "明星", "娱乐", "色情", "成人",
    "政治", "选举", "翻墙", "vpn",
    "身份证", "手机号", "护照", "信用卡", "password", "passwd",
    "api_key", "api-key", "token", "secret", "私钥", "私钥串",
)

_SENSITIVE_PATTERNS = (
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9\.\-_]+", re.IGNORECASE),
    re.compile(r"\b1\d{10}\b"),
    re.compile(r"\b\d{15,18}\b"),
)

_RATE_LIMIT_WINDOW_SEC = 60
_RATE_LIMIT_MAX_CALLS = 20
_call_timestamps: List[float] = []


def _check_blocklist(query: str) -> str:
    lower = (query or "").lower()
    for kw in _BLOCKED_KEYWORDS:
        if kw.lower() in lower:
            return f"query 命中黑名单关键字 '{kw}', 拒绝联网搜索"
    return ""


def _check_sensitive(query: str) -> str:
    for pattern in _SENSITIVE_PATTERNS:
        if pattern.search(query or ""):
            return "query 含敏感信息 (IP/token/手机号/身份证), 请脱敏后重试"
    return ""


def _check_rate_limit() -> str:
    now = time.time()
    cutoff = now - _RATE_LIMIT_WINDOW_SEC
    while _call_timestamps and _call_timestamps[0] < cutoff:
        _call_timestamps.pop(0)
    if len(_call_timestamps) >= _RATE_LIMIT_MAX_CALLS:
        return f"web_search 调用超过频率限制 ({_RATE_LIMIT_MAX_CALLS}/{_RATE_LIMIT_WINDOW_SEC}s)"
    _call_timestamps.append(now)
    return ""


# ============================================================
# Tool
# ============================================================
@mcp.tool(
    name="web_search",
    description=(
        "联网搜索互联网, 获取官方文档/技术资料/错误码说明等外部知识。"
        "仅用于 OnCall 运维诊断, 严禁用于娱乐/八卦/隐私查询; "
        "query 必须脱敏, 不能含 IP / token / 手机号 / 身份证等敏感信息。"
    ),
)
def web_search(query: str, max_results: int = 5) -> str:
    """联网搜索, 受黑名单 / 脱敏 / 限频三层硬约束保护."""
    query = (query or "").strip()
    if not query:
        return "[web_search] query 为空, 请提供具体的运维/技术问题"
    if len(query) > 200:
        return "[web_search] query 过长 (>200 字符), 请精简为关键关键词"

    blocked = _check_blocklist(query)
    if blocked:
        logger.warning(f"[web_search] BLOCK 黑名单: {blocked} | query={query!r}")
        return f"[web_search] 已拒绝: {blocked}. 本工具仅服务于 OnCall 运维诊断."

    sensitive = _check_sensitive(query)
    if sensitive:
        logger.warning(f"[web_search] BLOCK 敏感: {sensitive} | query={query!r}")
        return f"[web_search] 已拒绝: {sensitive}."

    rate = _check_rate_limit()
    if rate:
        logger.warning(f"[web_search] BLOCK 限频: {rate}")
        return f"[web_search] 已拒绝: {rate}, 请稍后再试."

    max_results = max(1, min(int(max_results or 5), 10))
    provider = get_provider()
    logger.info(f"[web_search] provider={provider} | query={query!r} | top={max_results}")

    try:
        results = search(query, max_results, provider)
    except Exception as e:
        logger.exception(f"[web_search] {provider} 搜索失败: {e}")
        return f"[web_search] 搜索失败 ({type(e).__name__}: {e}), 请基于已有信息推理或人工查官方文档"

    if not results:
        return f"[web_search] 未找到与 '{query}' 相关的结果, 请尝试换关键词"

    return format_results(results, provider=provider)


if __name__ == "__main__":
    print("[mcp] websearch_server starting on http://0.0.0.0:8006/mcp ...")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8006)
