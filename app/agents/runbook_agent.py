"""RunbookAgent —— Deep Diagnosis 的 SOP/Runbook 检索专业 subagent。

与 LogAgent 错位 (虽然两者都用 knowledge_tool):
  - LogAgent: 围绕"日志/告警异常模式"检索 (匹配日志模板 + 告警规则);
  - RunbookAgent: 围绕"处置流程/运维规范"检索 (匹配 SOP / 排查手册 / 操作步骤),
    输出"该类故障的标准 SOP 摘要", 供 RCAJudge / RemediationPlanner 参考。

s06 范式 (与 MetricAgent / LogAgent 对称)。失败必降级, 不抛, 不拖垮 deep graph。
"""

from typing import Any, Dict, List

from loguru import logger

from app.agents.state_deep import DeepDiagnosisState
from app.incidents.models import EvidenceSource
from app.runtime.transitions import DEEP_AGENT_DONE, make_transition


def _load_runbook_tools() -> List[Any]:
    """延迟导入: 与 LogAgent 同款工具, 但 scoped prompt 不同 (重点是流程而非告警)。"""
    from app.tools.knowledge_tool import search_knowledge_base
    return [search_knowledge_base]


_SYSTEM_PROMPT = (
    "你是 SRE 运维 SOP/Runbook 专家 (Runbook Agent), 隶属于一个多 Agent 诊断团队。\n"
    "关键边界: 你和 LogAgent 都用知识库, 但分工不同 —— LogAgent 关心『日志模式/告警规则』,\n"
    "你关心『处置流程 / 排查步骤 / 运维规范』。两者**不要重复内容**。\n\n"
    "你的职责: 围绕给定故障现象, 检索知识库找出**适用的 SOP / Runbook**, 把关键流程要点\n"
    "压成一段中文 summary, 供后续 RCAJudge / RemediationPlanner 参考。\n\n"
    "可用知识源 (内部混合, 你按关键词侧重):\n"
    "- Prometheus 告警规则附带的处置建议\n"
    "- 内部 OnCall SOP (Redis/MySQL/通用告警)\n"
    "- (loghub 日志模板尽量少看 —— 那是 LogAgent 的事)\n\n"
    "硬性约束:\n"
    "1. 检索关键词应含 'SOP / 处理流程 / 排查步骤 / 怎么处理 / runbook' 等流程类词;\n"
    "2. summary 必须: 点名命中的 SOP 来源 + 关键步骤 (3-5 条编号要点); 若无匹配明确说\n"
    "   '未命中适用的 SOP/Runbook'; <=400 字, 不展开所有流程细节;\n"
    "3. 最多 3 轮 LLM↔工具往返;\n"
    "4. 不要写『根因判定』或『处置命令』—— 那是别的 Agent 的事, 你只摘 SOP。"
)


def _build_user_prompt(incident_text: str) -> str:
    text = (incident_text or "").strip() or "(未提供现象, 检索通用 OnCall SOP)"
    return (
        "故障现象:\n"
        f"{text}\n\n"
        "请检索匹配的 SOP/Runbook, 摘要关键处置步骤 (≤400 字, 编号要点)。"
    )


def _summarize_messages(messages: List[Any]) -> tuple[str, List[Dict[str, Any]]]:
    last = messages[-1] if messages else None
    raw = getattr(last, "content", "") if last is not None else ""
    summary = (raw if isinstance(raw, str) else str(raw)).strip() or "(runbook_agent 无输出)"
    tool_calls: List[Dict[str, Any]] = []
    for m in messages or []:
        if getattr(m, "type", None) == "tool":
            tool_calls.append({
                "name": getattr(m, "name", ""),
                "preview": str(getattr(m, "content", ""))[:500],
            })
    return summary, tool_calls


def _evidence(summary: str, content: Dict[str, Any], *, tool_call_count: int, error: str = "") -> Dict[str, Any]:
    metadata: Dict[str, Any] = {"agent": "runbook_agent", "tool_call_count": tool_call_count}
    if error:
        metadata["error_type"] = error
    return {
        "source": str(EvidenceSource.RUNBOOK),
        "type": "runbook_match",
        "summary": summary[:2000],
        "content": content,
        "metadata": metadata,
    }


async def run_runbook_agent(state: DeepDiagnosisState) -> DeepDiagnosisState:
    """Deep graph 的 runbook_agent 节点入口 —— 检索 SOP 类知识, 与 LogAgent 错位。"""
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
            tools=_load_runbook_tools(),
            system_prompt=_SYSTEM_PROMPT,
            inputs={"messages": [("user", _build_user_prompt(incident_text))]},
            max_iters=3,
            max_parallel=2,
            decisions=None,
        )
        summary, tool_calls = _summarize_messages(result.get("messages") or [])
        logger.info(f"[deep] runbook_agent: tools={len(tool_calls)} summary={summary[:80]!r}")
        ev = _evidence(summary, content={"tool_calls": tool_calls, "task_id": task_id}, tool_call_count=len(tool_calls))
        return {
            "evidences": [ev],
            "transition_history": [make_transition("runbook_agent", DEEP_AGENT_DONE, f"tools={len(tool_calls)}")],
        }
    except Exception as exc:
        logger.exception(f"[deep] runbook_agent failed: {exc}")
        ev = _evidence(
            summary=f"runbook_agent 执行失败: {type(exc).__name__}: {exc}",
            content={"error": True, "task_id": task_id},
            tool_call_count=0,
            error=type(exc).__name__,
        )
        return {
            "evidences": [ev],
            "transition_history": [make_transition("runbook_agent", DEEP_AGENT_DONE, f"error: {type(exc).__name__}")],
        }
