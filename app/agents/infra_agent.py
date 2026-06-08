"""InfraAgent —— Deep Diagnosis 的运行环境 / 依赖健康专业 subagent。

与 MetricAgent 错位:
  - MetricAgent 关心 CPU / 内存 / 磁盘 / 进程等资源指标;
  - InfraAgent 关心容器状态、端口可达性、DNS / HTTP 健康和基础依赖状态。

只使用只读工具。即使 Docker / Network MCP 未连接，也会退化成本机系统快照，
不影响 deep graph 继续输出报告。
"""

from typing import Any, Dict, List

from loguru import logger

from app.agents.state_deep import DeepDiagnosisState
from app.incidents.models import EvidenceSource
from app.runtime.transitions import DEEP_AGENT_DONE, make_transition


_MCP_INFRA_TOOL_NAMES = {
    "docker_ps",
    "docker_stats",
    "docker_logs",
    "docker_inspect",
    "dns_lookup",
    "http_check",
    "check_port",
}


def _load_infra_tools() -> List[Any]:
    """加载运行环境只读工具。

    本地 system 工具永远可用；Docker / Network 工具来自 MCP，已连接时加入。
    明确不加入 docker_restart 等写操作。
    """
    from app.core.mcp_client import mcp_client_manager
    from app.tools.system_tool import (
        get_local_disk_usage,
        get_local_system_overview,
        list_top_processes,
    )

    tools: List[Any] = [
        get_local_system_overview,
        get_local_disk_usage,
        list_top_processes,
    ]
    seen = {tool.name for tool in tools if getattr(tool, "name", "")}

    for tool in mcp_client_manager.tools:
        name = getattr(tool, "name", "")
        if name in _MCP_INFRA_TOOL_NAMES and name not in seen:
            tools.append(tool)
            seen.add(name)
    return tools


_SYSTEM_PROMPT = (
    "你是 SRE 基础设施/依赖健康专家 (Infra Agent), 隶属于一个多 Agent 诊断团队。\n"
    "你的职责: 围绕给定故障现象, 只读检查运行环境和基础依赖, 包括容器状态、端口、"
    "DNS/HTTP 健康、本机磁盘和关键进程。你不负责资源指标细节、日志模式检索或 SOP 摘要。\n\n"
    "硬性约束:\n"
    "1. 只能做只读取证, 不要调用重启、删除、修改配置等写操作。\n"
    "2. 优先判断服务是否没起来、容器是否重启、端口是否不通、DNS/HTTP 是否异常。\n"
    "3. 若 Docker / Network 工具不可用, 明确说明只完成了本机运行环境快照, 不要编造外部依赖结果。\n"
    "4. summary 必须点名关键异常或明确说未观察到基础设施异常, <=350 字。"
)


def _build_user_prompt(incident_text: str) -> str:
    text = (incident_text or "").strip() or "(未提供现象, 默认检查本机运行环境和依赖健康)"
    return (
        "故障现象:\n"
        f"{text}\n\n"
        "请按上述约束做基础设施/依赖健康取证, 输出一段 summary。"
    )


def _summarize_messages(messages: List[Any]) -> tuple[str, List[Dict[str, Any]]]:
    last = messages[-1] if messages else None
    raw = getattr(last, "content", "") if last is not None else ""
    summary = (raw if isinstance(raw, str) else str(raw)).strip() or "(infra_agent 无输出)"

    tool_calls: List[Dict[str, Any]] = []
    for msg in messages or []:
        if getattr(msg, "type", None) == "tool":
            tool_calls.append({
                "name": getattr(msg, "name", ""),
                "preview": str(getattr(msg, "content", ""))[:500],
            })
    return summary, tool_calls


def _evidence(summary: str, content: Dict[str, Any], *, tool_call_count: int, error: str = "") -> Dict[str, Any]:
    metadata: Dict[str, Any] = {"agent": "infra_agent", "tool_call_count": tool_call_count}
    if error:
        metadata["error_type"] = error
    return {
        "source": str(EvidenceSource.MCP_TOOL_RESULT),
        "type": "infra_snapshot",
        "summary": summary[:2000],
        "content": content,
        "metadata": metadata,
    }


async def run_infra_agent(state: DeepDiagnosisState) -> DeepDiagnosisState:
    """Deep graph 的 infra_agent 节点入口。"""
    incident_text = state.get("input") or ""
    task_id = state.get("task_id") or ""

    try:
        from app.core.llm import get_chat_llm
        from app.runtime.agent_harness import get_agent_harness
        from app.runtime.tool_runner import run_parallel_agent

        harness = get_agent_harness()
        llm = get_chat_llm(model=harness.executor_model(), temperature=0, streaming=False)
        result = await run_parallel_agent(
            llm=llm,
            tools=_load_infra_tools(),
            system_prompt=_SYSTEM_PROMPT,
            inputs={"messages": [("user", _build_user_prompt(incident_text))]},
            max_iters=4,
            max_parallel=4,
            decisions=None,
        )
        summary, tool_calls = _summarize_messages(result.get("messages") or [])
        logger.info(f"[deep] infra_agent: tools={len(tool_calls)} summary={summary[:80]!r}")
        ev = _evidence(
            summary,
            content={"tool_calls": tool_calls, "task_id": task_id},
            tool_call_count=len(tool_calls),
        )
        return {
            "evidences": [ev],
            "transition_history": [make_transition("infra_agent", DEEP_AGENT_DONE, f"tools={len(tool_calls)}")],
        }
    except Exception as exc:
        logger.exception(f"[deep] infra_agent failed: {exc}")
        ev = _evidence(
            summary=f"infra_agent 执行失败: {type(exc).__name__}: {exc}",
            content={"error": True, "task_id": task_id},
            tool_call_count=0,
            error=type(exc).__name__,
        )
        return {
            "evidences": [ev],
            "transition_history": [make_transition("infra_agent", DEEP_AGENT_DONE, f"error: {type(exc).__name__}")],
        }
