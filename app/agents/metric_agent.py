"""MetricAgent —— Deep Diagnosis (群聊 / M7) 的指标专业 subagent。

s06 范式 (借鉴 learn-claude-code 课程, 见 COURSE_SUMMARY.md):
  - 一次性、隔离上下文、自己跑最小 LLM+工具循环 (run_parallel_agent);
  - 不读共享 state 的中间过程, 只读 scoped 输入 (input + task 元信息);
  - 中间推理 (内部 messages[]) 不进共享 state, 只把结论压成一条 Evidence 返回;
  - 失败必降级 (返回带 error metadata 的占位 Evidence), 不抛, 不拖垮 deep graph。

工具白名单 (硬编码): 4 个本机 read-only 指标工具
  get_local_system_overview / get_local_cpu_memory /
  get_local_disk_usage / list_top_processes

为什么硬编码而不走 fast 的 filter_tools_for_skill:
  - skill 过滤是 fast Plan-Execute 的概念, 与"专业 Agent 自带工具白名单"是不同范式;
  - 骨架阶段先让 Agent 形态契约清晰可见, 不混入 skill 路由;
  - 本机 system 工具全是 read-only, 跳过 PermissionMode 在骨架阶段安全可控。

TODO(M7+):
  - 真后端: 接 Prometheus / VictoriaMetrics 等真 metric 数据源 (本机指标是骨架演示);
  - 权限: 接入 PermissionMode (现在 decisions=None 走 run_parallel_agent 的向后兼容路径);
  - 复用: 若多个专业 Agent 都需要"scoped LLM 循环 + Evidence 压制", 抽 specialist_runner 公共层。
"""

from typing import Any, Dict, List

from loguru import logger

from app.agents.state_deep import DeepDiagnosisState
from app.incidents.models import EvidenceSource
from app.runtime.transitions import DEEP_AGENT_DONE, make_transition


def _load_metric_tools() -> List[Any]:
    """延迟导入: 避免 deep_diagnosis_graph 模块加载时就拉起 langchain @tool。

    顺序原则: Prometheus (真后端) 优先, 本机 system 工具兜底.
    Prom 未配置时 get_prom_tools() 返回 [], 自动退化为纯本机集合.
    """
    from app.tools.prom_tool import get_prom_tools
    from app.tools.system_tool import (
        get_local_cpu_memory,
        get_local_disk_usage,
        get_local_system_overview,
        list_top_processes,
    )
    prom_tools = get_prom_tools()
    local_tools = [
        get_local_system_overview,
        get_local_cpu_memory,
        get_local_disk_usage,
        list_top_processes,
    ]
    # Prom 工具排在前: LLM 看到工具列表会优先尝试真指标, 失败再走本机.
    return [*prom_tools, *local_tools]


_SYSTEM_PROMPT = (
    "你是 SRE 指标专家 (Metric Agent), 隶属于一个多 Agent 诊断团队中的专业子 Agent。\n"
    "你的职责: 围绕给定的故障现象, 调用指标采集工具, 拿到结构化指标快照, "
    "找出**异常项**并压成一段中文 summary。\n\n"
    "硬性约束:\n"
    "1. 只用本机指标采集工具 (CPU/内存/磁盘/进程), 不要谈日志/调用链/处置建议——那是别的 Agent 的事。\n"
    "2. summary 必须: 点名异常项及其指标值; 若无异常明确说\"未观察到异常\"; 不罗列全部数据, 只点关键 (<=300 字)。\n"
    "3. 最多 4 轮 LLM↔工具往返, 拿到必要数据就停, 不要漫游。\n"
    "4. 工具失败时直接说\"工具不可用\", 不要编造数据。"
)


def _build_user_prompt(incident_text: str) -> str:
    text = (incident_text or "").strip() or "(未提供现象, 默认采全量本机指标快照)"
    return (
        "故障现象:\n"
        f"{text}\n\n"
        "请按上述约束采集本机指标, 找异常, 输出一段 summary。"
    )


def _summarize_messages(messages: List[Any]) -> tuple[str, List[Dict[str, Any]]]:
    """从 run_parallel_agent 输出取最后 AI 消息 + 中间 tool 调用摘要。"""
    last_msg = messages[-1] if messages else None
    raw = getattr(last_msg, "content", "") if last_msg is not None else ""
    summary = (raw if isinstance(raw, str) else str(raw)).strip() or "(metric_agent 无输出)"

    tool_calls: List[Dict[str, Any]] = []
    for m in messages or []:
        # langchain ToolMessage 的 type=="tool"
        if getattr(m, "type", None) == "tool":
            preview = str(getattr(m, "content", ""))[:500]
            tool_calls.append({"name": getattr(m, "name", ""), "preview": preview})
    return summary, tool_calls


def _evidence(summary: str, content: Dict[str, Any], *, tool_call_count: int, error: str = "") -> Dict[str, Any]:
    """构造一条 metric_snapshot Evidence (与 EvidenceCreate 字段对齐, dict 形式)。"""
    metadata: Dict[str, Any] = {"agent": "metric_agent", "tool_call_count": tool_call_count}
    if error:
        metadata["error_type"] = error
    return {
        "source": str(EvidenceSource.METRIC),
        "type": "metric_snapshot",
        "summary": summary[:2000],
        "content": content,
        "metadata": metadata,
    }


async def run_metric_agent(state: DeepDiagnosisState) -> DeepDiagnosisState:
    """Deep graph 的 metric_agent 节点入口 —— 真实隔离 subagent。

    与 PlanExecuteState 完全解耦, 不读 plan/past_steps; 只读 input 作为现象描述。
    输出: 1 条 metric_snapshot Evidence (合并进 evidences 累加器) +
    1 条 transition (供 SSE 时间线渲染)。
    """
    incident_text = state.get("input") or ""
    task_id = state.get("task_id") or ""

    try:
        # 延迟导入放在 try 内: 任何依赖 (langchain/pydantic/core.llm) 缺失或加载失败,
        # 都直接落到下面的 except 降级路径, 而不是把异常抛回 LangGraph 顶层导致整图崩。
        from app.core.llm import get_chat_llm
        from app.runtime.agent_harness import get_agent_harness
        from app.runtime.tool_runner import run_parallel_agent

        harness = get_agent_harness()
        llm = get_chat_llm(
            model=harness.executor_model(),  # 复用 executor 模型档位 (推荐 flash, 便宜快)
            temperature=0,
            streaming=False,  # 不需要流式: 是 subagent 内部循环, 不直接面向 SSE
        )
        result = await run_parallel_agent(
            llm=llm,
            tools=_load_metric_tools(),
            system_prompt=_SYSTEM_PROMPT,
            inputs={"messages": [("user", _build_user_prompt(incident_text))]},
            max_iters=4,            # 比 fast Executor 严格 (4 轮足以采完本机 4 个工具)
            max_parallel=4,         # 4 个 read-only 工具同批 gather
            decisions=None,         # TODO: 接 PermissionMode (本机 read-only 工具骨架阶段安全)
        )
        summary, tool_calls = _summarize_messages(result.get("messages") or [])
        logger.info(
            f"[deep] metric_agent: tools={len(tool_calls)} summary={summary[:80]!r}"
        )
        ev = _evidence(
            summary,
            content={"tool_calls": tool_calls, "task_id": task_id},
            tool_call_count=len(tool_calls),
        )
        return {
            "evidences": [ev],
            "transition_history": [
                make_transition("metric_agent", DEEP_AGENT_DONE, f"tools={len(tool_calls)}")
            ],
        }
    except Exception as exc:
        # 降级: 不抛, 让 deep graph 继续走完; 但 Evidence 标错误, 供 RCAJudge 识别。
        logger.exception(f"[deep] metric_agent failed: {exc}")
        ev = _evidence(
            summary=f"metric_agent 执行失败: {type(exc).__name__}: {exc}",
            content={"error": True, "task_id": task_id},
            tool_call_count=0,
            error=type(exc).__name__,
        )
        return {
            "evidences": [ev],
            "transition_history": [
                make_transition("metric_agent", DEEP_AGENT_DONE, f"error: {type(exc).__name__}")
            ],
        }
