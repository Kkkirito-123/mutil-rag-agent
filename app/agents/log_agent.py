"""LogAgent —— Deep Diagnosis (群聊 / M7) 的日志/知识检索专业 subagent。

s06 范式 (与 MetricAgent 对称, 见 COURSE_SUMMARY.md):
  - 一次性、隔离上下文、自己跑最小 LLM+工具循环 (run_parallel_agent);
  - 不读共享 state 的中间过程, 只读 scoped 输入 (input + task 元信息);
  - 中间推理 (内部 messages[]) 不进共享 state, 只把结论压成一条 Evidence 返回;
  - 失败必降级 (返回带 error metadata 的占位 Evidence), 不抛, 不拖垮 deep graph。

工具白名单 (硬编码): 1 个 knowledge_tool.search_knowledge_base
  - 知识库已含: 951 个 Prometheus 告警规则 + 669 个 loghub 日志模板 + 3 个 OnCall SOP
  - 这一刀首次把"知识侧资产"用进"诊断侧" —— LogAgent 不读原始日志 (8.2G 不进库),
    而是去 RAG 命中"该现象对应的日志模板和告警规则", 把匹配结果压成 log_excerpt Evidence。

与 MetricAgent 的差异:
  - max_iters=3 (RAG 查询通常 1-2 次足够; metric 要采多个工具)
  - max_parallel=2 (只有 1 个工具, 实际无并行)
  - Evidence type=log_excerpt (vs metric_snapshot)
  - source=LOG (vs METRIC)

TODO(M7+):
  - 真后端: 接 Loki / Elasticsearch 等真日志后端 (现在只检索"日志模板", 不查原始日志);
  - 权限: 接入 PermissionMode (search_knowledge_base 是 read-only, 骨架阶段安全);
  - 抽象: 若多个专业 Agent 都需要"RAG + 压制 Evidence", 抽 specialist_runner 公共层。
"""

from typing import Any, Dict, List

from loguru import logger

from app.agents.state_deep import DeepDiagnosisState
from app.incidents.models import EvidenceSource
from app.runtime.transitions import DEEP_AGENT_DONE, make_transition


def _load_log_tools() -> List[Any]:
    """延迟导入: 避免 deep_diagnosis_graph 装配时拉起 langchain @tool 子树。"""
    from app.tools.knowledge_tool import search_knowledge_base
    return [search_knowledge_base]


_SYSTEM_PROMPT = (
    "你是 SRE 日志/知识检索专家 (Log Agent), 隶属于一个多 Agent 诊断团队中的专业子 Agent。\n"
    "你的职责: 围绕给定的故障现象, 调用知识库检索工具, 命中相关的**日志模板**、"
    "**告警规则**或**排障 SOP**, 找出与现象**匹配**的模式, 并压成一段中文 summary。\n\n"
    "可用知识源 (search_knowledge_base 内部已混合):\n"
    "- Prometheus 告警规则 (含 PromQL 和处理建议)\n"
    "- loghub-2.0 日志模板 (HDFS/Spark/BGL/OpenSSH/Apache 共 669 个模板)\n"
    "- 内部 OnCall SOP (Redis/MySQL/通用告警)\n\n"
    "硬性约束:\n"
    "1. 只用知识库检索工具, 不要谈指标/调用链/处置建议——那是别的 Agent 的事。\n"
    "2. summary 必须: 点名命中的关键模板/规则及其来源; 若无匹配明确说\"未命中相关日志模式\"; "
    "不罗列全部检索结果, 只点关键 (<=300 字)。\n"
    "3. 最多 3 轮 LLM↔工具往返, 命中即停, 不要漫游。\n"
    "4. 工具失败时直接说\"知识库不可用\", 不要编造。"
)


def _build_user_prompt(incident_text: str) -> str:
    text = (incident_text or "").strip() or "(未提供现象, 默认检索通用 OnCall 知识)"
    return (
        "故障现象:\n"
        f"{text}\n\n"
        "请按上述约束去知识库检索匹配的日志模板/告警规则/SOP, 输出一段 summary。"
    )


def _summarize_messages(messages: List[Any]) -> tuple[str, List[Dict[str, Any]]]:
    """从 run_parallel_agent 输出取最后 AI 消息 + 中间 tool 调用摘要。"""
    last_msg = messages[-1] if messages else None
    raw = getattr(last_msg, "content", "") if last_msg is not None else ""
    summary = (raw if isinstance(raw, str) else str(raw)).strip() or "(log_agent 无输出)"

    tool_calls: List[Dict[str, Any]] = []
    for m in messages or []:
        if getattr(m, "type", None) == "tool":
            preview = str(getattr(m, "content", ""))[:500]
            tool_calls.append({"name": getattr(m, "name", ""), "preview": preview})
    return summary, tool_calls


def _evidence(summary: str, content: Dict[str, Any], *, tool_call_count: int, error: str = "") -> Dict[str, Any]:
    """构造一条 log_excerpt Evidence (与 EvidenceCreate 字段对齐)。"""
    metadata: Dict[str, Any] = {"agent": "log_agent", "tool_call_count": tool_call_count}
    if error:
        metadata["error_type"] = error
    return {
        "source": str(EvidenceSource.LOG),
        "type": "log_excerpt",
        "summary": summary[:2000],
        "content": content,
        "metadata": metadata,
    }


async def run_log_agent(state: DeepDiagnosisState) -> DeepDiagnosisState:
    """Deep graph 的 log_agent 节点入口 —— 隔离 subagent 调 RAG 检索。

    与 PlanExecuteState 完全解耦; 只读 input 作为现象描述。
    输出: 1 条 log_excerpt Evidence (合并进 evidences 累加器) + 1 条 transition。
    """
    incident_text = state.get("input") or ""
    task_id = state.get("task_id") or ""

    try:
        # 延迟 import 全放 try 内: langchain/llm/RAG 任意缺失都直接走降级。
        from app.core.llm import get_chat_llm
        from app.runtime.agent_harness import get_agent_harness
        from app.runtime.tool_runner import run_parallel_agent

        harness = get_agent_harness()
        llm = get_chat_llm(
            model=harness.executor_model(),  # 复用 executor 模型档位
            temperature=0,
            streaming=False,
        )
        result = await run_parallel_agent(
            llm=llm,
            tools=_load_log_tools(),
            system_prompt=_SYSTEM_PROMPT,
            inputs={"messages": [("user", _build_user_prompt(incident_text))]},
            max_iters=3,            # RAG 查询 1-2 次够, 比 metric 严格
            max_parallel=2,         # 只 1 个工具实际无并行
            decisions=None,         # TODO: 接 PermissionMode (search_knowledge_base 是 read-only)
        )
        summary, tool_calls = _summarize_messages(result.get("messages") or [])
        logger.info(
            f"[deep] log_agent: tools={len(tool_calls)} summary={summary[:80]!r}"
        )
        ev = _evidence(
            summary,
            content={"tool_calls": tool_calls, "task_id": task_id},
            tool_call_count=len(tool_calls),
        )
        return {
            "evidences": [ev],
            "transition_history": [
                make_transition("log_agent", DEEP_AGENT_DONE, f"tools={len(tool_calls)}")
            ],
        }
    except Exception as exc:
        # 降级: 不抛, deep graph 继续走; Evidence 标 error 供 RCAJudge 识别。
        logger.exception(f"[deep] log_agent failed: {exc}")
        ev = _evidence(
            summary=f"log_agent 执行失败: {type(exc).__name__}: {exc}",
            content={"error": True, "task_id": task_id},
            tool_call_count=0,
            error=type(exc).__name__,
        )
        return {
            "evidences": [ev],
            "transition_history": [
                make_transition("log_agent", DEEP_AGENT_DONE, f"error: {type(exc).__name__}")
            ],
        }
