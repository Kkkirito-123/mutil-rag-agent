"""Prometheus HTTP API @tool 集 (按需启用).

设计思路:
  - 用 settings.prometheus_url 做开关; 留空 = 未配置, 工具返回友好提示而不是炸栈,
    让 LLM 知道"这台没接 Prom, 请改用本机指标工具".
  - 任何网络/HTTP/解析错误都吞掉, 转成 markdown 错误说明返回; 上游 Agent 看到
    错误后会自动降级到本机 (system_tool) 路径, 诊断主链路不被打断.
  - 4 个工具覆盖 80% PromQL 场景: instant / range / alerts / label_values.
  - 全部 read_only=True / concurrency_safe=True, 由 meta.py 集中登记.

未做的事 (留给后续迭代):
  - HTTP Basic Auth / Bearer Token: 现在只支持开放 Prometheus, 加密 Prom 需要扩 settings
  - Pushgateway / Federation / OpenMetrics 写入: 与 read-only 定位不符
  - VictoriaMetrics 自有 API (/api/v1/series 等): 兼容层只覆盖 Prom 标准 API
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

from langchain_core.tools import tool
from loguru import logger

from app.config import settings


# ============================================================
# 内部辅助
# ============================================================
def _not_configured_md(action: str) -> str:
    """Prom URL 没配时的统一返回.

    主调用方 (MetricAgent / 任何 Skill) 看到这段会知道走本机指标兜底, 不会再继续等.
    """
    return (
        f"## Prometheus 未配置\n"
        f"无法执行 `{action}`: 当前 PROMETHEUS_URL 为空 (或 .env 未设置).\n\n"
        f"如需启用真实指标后端, 在 `.env` 中加:\n"
        f"```\nPROMETHEUS_URL=http://prometheus.example:9090\n```\n"
        f"未配置时请改用本机指标工具 (get_local_system_overview / get_local_cpu_memory)."
    )


def _error_md(action: str, exc: BaseException) -> str:
    return (
        f"## Prometheus 调用失败\n"
        f"动作: `{action}`\n"
        f"错误类型: `{type(exc).__name__}`\n"
        f"错误信息: {exc}\n\n"
        f"建议: 降级到本机 metric 工具, 或检查 PROMETHEUS_URL 与网络连通性."
    )


async def _http_get(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """统一封装 Prometheus HTTP API 调用. 失败抛, 由调用方 catch 转 markdown."""
    import httpx  # 延迟导入: httpx 是 FastAPI 强依赖, 一定有, 但留延迟导入便于将来替换

    base = settings.prometheus_url.rstrip("/")
    url = f"{base}{path}"
    timeout = float(getattr(settings, "prometheus_timeout_sec", 8.0))
    async with httpx.AsyncClient(timeout=timeout) as cli:
        resp = await cli.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
    if data.get("status") != "success":
        # Prom 标准错误体: {status: "error", errorType: "bad_data", error: "..."}
        raise RuntimeError(f"prom error: {data.get('errorType')}: {data.get('error')}")
    return data.get("data") or {}


def _format_vector(result: List[Dict[str, Any]], limit: int = 25) -> str:
    """instant query 返回的 vector / scalar 结构 → markdown 表."""
    if not result:
        return "(无数据)"
    lines = ["| metric | value | timestamp |", "|---|---|---|"]
    for item in result[:limit]:
        metric = item.get("metric") or {}
        value = item.get("value") or [None, None]
        ts, val = value if len(value) == 2 else (None, None)
        label = ", ".join(f"{k}={v}" for k, v in sorted(metric.items()) if k != "__name__") or "—"
        name = metric.get("__name__") or "expr"
        lines.append(f"| `{name}{{{label}}}` | {val} | {ts} |")
    extra = len(result) - limit
    if extra > 0:
        lines.append(f"| _… 还有 {extra} 行被截断_ |  |  |")
    return "\n".join(lines)


def _format_matrix(result: List[Dict[str, Any]], max_series: int = 6, max_points: int = 12) -> str:
    """range query 返回的 matrix 结构 → 每个 series 最近 N 个点的简表."""
    if not result:
        return "(无时间序列)"
    parts: List[str] = []
    for series in result[:max_series]:
        metric = series.get("metric") or {}
        values = series.get("values") or []
        name = metric.get("__name__") or "expr"
        label = ", ".join(f"{k}={v}" for k, v in sorted(metric.items()) if k != "__name__") or "—"
        tail = values[-max_points:]
        sample = " ".join(f"{v}@{int(float(ts))}" for ts, v in tail)
        parts.append(f"- `{name}{{{label}}}` → {sample}")
    if len(result) > max_series:
        parts.append(f"- _… 还有 {len(result) - max_series} 个 series 被截断_")
    return "\n".join(parts)


# ============================================================
# Public @tool 入口
# ============================================================

@tool
async def prom_query(promql: str) -> str:
    """对 Prometheus 执行 instant query (`/api/v1/query`).

    适合: 取当前瞬时值, 比如 `up`, `process_cpu_seconds_total`,
    `rate(http_requests_total[1m])`.

    参数:
      promql: 任意合法 PromQL 表达式 (不要带时间范围, 即时查询用).

    返回 markdown 表 (metric / value / timestamp) 或错误说明.
    """
    if not settings.prometheus_url:
        return _not_configured_md(f"prom_query({promql})")
    try:
        data = await _http_get("/api/v1/query", {"query": promql})
        result_type = data.get("resultType")
        result = data.get("result") or []
        head = f"## PromQL: `{promql}`\n类型: `{result_type}` · 命中 {len(result)} 行\n\n"
        if result_type in ("vector", "scalar"):
            body = _format_vector(result if result_type == "vector" else [{"metric": {}, "value": result}])
        else:
            body = "(未知结果类型, 原始: " + str(result)[:400] + ")"
        return head + body
    except Exception as exc:
        logger.warning(f"[prom] query failed promql={promql!r}: {exc}")
        return _error_md(f"prom_query({promql})", exc)


@tool
async def prom_query_range(promql: str, lookback_seconds: int = 600, step_seconds: int = 30) -> str:
    """对 Prometheus 执行 range query (`/api/v1/query_range`), 看一段时间的趋势.

    适合: 看最近 N 分钟的曲线, 比如 CPU 使用率/请求 QPS/错误率随时间变化.

    参数:
      promql: PromQL 表达式 (通常是 rate(...) / sum by (svc)(...) 之类).
      lookback_seconds: 往前看多少秒 (默认 600 = 10 分钟).
      step_seconds: 采样间隔秒数 (默认 30).

    返回 markdown: 每个 series 最近若干点的简表. 错误时返回错误说明.
    """
    if not settings.prometheus_url:
        return _not_configured_md(f"prom_query_range({promql})")
    try:
        end = int(time.time())
        start = end - max(60, int(lookback_seconds))
        step = max(5, int(step_seconds))
        data = await _http_get(
            "/api/v1/query_range",
            {"query": promql, "start": start, "end": end, "step": step},
        )
        result = data.get("result") or []
        head = (
            f"## PromQL range: `{promql}`\n"
            f"窗口: 最近 {lookback_seconds}s · step {step}s · series {len(result)}\n\n"
        )
        return head + _format_matrix(result)
    except Exception as exc:
        logger.warning(f"[prom] query_range failed promql={promql!r}: {exc}")
        return _error_md(f"prom_query_range({promql})", exc)


@tool
async def prom_active_alerts() -> str:
    """列出 Prometheus 当前 firing 的告警 (`/api/v1/alerts`).

    适合: 入场了解"现在系统在烧什么", 给 Planner 一个全局视图.
    返回 markdown 表, 含 alertname / severity / service / 持续时间 / labels 摘要.
    """
    if not settings.prometheus_url:
        return _not_configured_md("prom_active_alerts()")
    try:
        data = await _http_get("/api/v1/alerts", {})
        alerts = data.get("alerts") or []
        if not alerts:
            return "## Prometheus 活跃告警\n(无 firing 告警)"
        lines = ["## Prometheus 活跃告警", "", "| alertname | severity | service / instance | active_since | state |", "|---|---|---|---|---|"]
        for a in alerts[:50]:
            labels = a.get("labels") or {}
            name = labels.get("alertname", "?")
            sev = labels.get("severity", "?")
            svc = labels.get("service") or labels.get("job") or labels.get("instance") or "—"
            since = a.get("activeAt", "?")
            state = a.get("state", "?")
            lines.append(f"| {name} | {sev} | {svc} | {since} | {state} |")
        if len(alerts) > 50:
            lines.append(f"| _… 还有 {len(alerts) - 50} 条被截断_ |  |  |  |  |")
        return "\n".join(lines)
    except Exception as exc:
        logger.warning(f"[prom] active_alerts failed: {exc}")
        return _error_md("prom_active_alerts()", exc)


@tool
async def prom_label_values(label: str, match: str = "") -> str:
    """列出某个 label 的所有取值 (`/api/v1/label/{label}/values`), 用于发现服务/实例.

    适合: 先 `prom_label_values('job')` 看有哪些服务, 再针对性写 PromQL.

    参数:
      label: 要列出取值的 label 名, 例如 `job` / `service` / `instance`.
      match: 可选, 限定匹配集的 series selector, 例如 `up` 或 `{namespace="prod"}`.
    """
    if not settings.prometheus_url:
        return _not_configured_md(f"prom_label_values({label})")
    try:
        params: Dict[str, Any] = {}
        if match:
            params["match[]"] = match
        data = await _http_get(f"/api/v1/label/{label}/values", params)
        # 这个接口比较特殊: data 直接是一个 list, 而不是 {result: [...]}
        values = data if isinstance(data, list) else (data.get("data") or [])
        if not values:
            return f"## label `{label}` 的取值\n(无)"
        head = f"## label `{label}` 的取值 ({len(values)} 个)\n\n"
        body = "\n".join(f"- `{v}`" for v in values[:200])
        if len(values) > 200:
            body += f"\n- _… 还有 {len(values) - 200} 个被截断_"
        return head + body
    except Exception as exc:
        logger.warning(f"[prom] label_values failed label={label!r}: {exc}")
        return _error_md(f"prom_label_values({label})", exc)


def get_prom_tools() -> List[Any]:
    """统一导出: MetricAgent / Skill 用这个拉一组工具.

    返回空列表表示未配置 (调用方自行决定要不要回退到本机工具).
    """
    if not settings.prometheus_url:
        return []
    return [prom_query, prom_query_range, prom_active_alerts, prom_label_values]


def is_configured() -> bool:
    return bool(settings.prometheus_url)
