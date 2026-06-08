"""把一条告警/诊断输入归一成「同类问题指纹」。

这是一个**通用的告警指纹工具**(原先放在 reflection/ 下, 简化后上移到 incidents/):
  - LLM Wiki recall_block 用它做"同类故障"的直达页查找 (patterns/<sig>.md);
  - 任何需要"同类告警聚到一起"的地方都可复用。

当前规则(保守版): 指纹 = "alertname|service", 全小写去空白。
  - 故意不含 instance / 时间 / 具体数值: 让"同一类故障"跨实例、跨时间聚到一起。
  - 取不到 alertname 时退化用 query 的前若干词(手动诊断入口没有 alertname)。
  - 实在没有可用信息则返回 "" —— 调用方应据此跳过。
"""

from __future__ import annotations

import re
from typing import Any

_WS = re.compile(r"\s+")


def _norm(text: Any) -> str:
    return _WS.sub(" ", str(text or "").strip().lower())


def alert_view(payload: dict[str, Any] | None) -> dict[str, Any]:
    """把一行 task.payload 收敛成"算指纹的规范输入"。

    只取建任务时写入、之后不再改动的告警侧稳定字段: alertname/service/severity/
    instance/query/summary。写入侧与读取侧必须对同一行 payload 过同一个 shaping,
    否则会"写得进、召不回"。
    """
    payload = payload or {}
    return {
        "alertname": str(payload.get("alertname") or ""),
        "service": str(payload.get("service") or ""),
        "severity": str(payload.get("severity") or ""),
        "instance": str(payload.get("instance") or ""),
        "query": str(payload.get("query") or ""),
        "summary": str(payload.get("summary") or ""),
    }


def compute_alert_signature(payload: dict[str, Any] | None) -> str:
    """从告警 payload 计算同类问题指纹; 无可用信息时返回空串。

    输入既可是 alert_view 的输出(推荐, 两侧同源), 也可是原始告警 dict(带 labels)。
    """
    payload = payload or {}
    labels = payload.get("labels") if isinstance(payload.get("labels"), dict) else {}

    alertname = _norm(payload.get("alertname") or labels.get("alertname"))
    service = _norm(payload.get("service") or labels.get("service"))

    if not alertname:
        # 手动诊断没有结构化告警, 用 query/summary 的前 8 个词当近似指纹。
        text = _norm(payload.get("query") or payload.get("summary"))
        alertname = " ".join(text.split()[:8])

    if not alertname and not service:
        return ""
    return f"{alertname}|{service}"
