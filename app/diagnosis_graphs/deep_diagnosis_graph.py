"""Deep Diagnosis Graph。

该图独立于 fast 的 Plan-Execute-Replan 链路。它负责把一次告警拆成事件上下文、
证据计划、专业 Agent 取证、证据归并、RCA 判断、处置建议和最终报告。

图结构:

    [START]
       │
       ▼
  IncidentManager      载入诊断对象 (task/incident)
       │
       ▼
  CorrelationContext   聚合同组告警、相邻事件和 Wiki 经验
       │
       ▼
  EvidencePlan         识别故障域 -> 决定派哪几个专业 subagent + 取证策略
       │
   ┌───┼───────┬───────────┐         ← fan-out (并行)
   ▼   ▼       ▼           ▼
 Log Metric  Infra      Runbook      各跑自己的隔离最小循环, 只回 Evidence (s06 subagent)
   └───┴───┬───┴───────────┘         ← fan-in (LangGraph 多入边 = join barrier)
           ▼
  EvidenceReducer      归并去重 -> 候选根因 + 证据路径
           ▼
  RCAJudge             只看结构化证据排序定根因
           ▼
  RemediationPlanner   出处置建议 (写操作 requires_human_confirm=True)
           ▼
  ReportAgent          报告, 结论引用 evidence_id; 填 response 触发 [END]

专业 Agent 是隔离的一次性取证节点，只把 Evidence 写回共享 state；中间推理不进入
共享上下文。
"""

from typing import Any

from langgraph.graph import END, START, StateGraph
from loguru import logger

from app.agents.state_deep import DeepDiagnosisState
from app.incidents.models import EvidenceSource
from app.runtime.transitions import (
    DEEP_AGENT_DONE,
    DEEP_CONTEXT_BUILT,
    DEEP_EVIDENCE_PLANNED,
    DEEP_EVIDENCE_REDUCED,
    DEEP_INCIDENT_LOADED,
    DEEP_RCA_JUDGED,
    DEEP_REMEDIATION_PLANNED,
    DEEP_REPORT_DONE,
    DEEP_STUB,
    make_transition,
)

# 专业 subagent 配置: (节点名, Evidence 来源, Evidence 类型)
# 真实实现里每个都是一个隔离的调查型 subagent, 只产对应类型的 Evidence。
# 真实节点函数由 _resolve_specialist_node_fn 按节点名延迟解析。
# 当前公开版保留的专业 Agent 都有可执行的数据来源；_make_specialist_node 仅作
# 未来扩展兜底。
SPECIALISTS = (
    ("log_agent", EvidenceSource.LOG, "log_excerpt"),
    ("metric_agent", EvidenceSource.METRIC, "metric_snapshot"),
    ("infra_agent", EvidenceSource.MCP_TOOL_RESULT, "infra_snapshot"),
    ("runbook_agent", EvidenceSource.RUNBOOK, "runbook_match"),
)


def _resolve_specialist_node_fn(name: str, source: EvidenceSource, etype: str):
    """按节点名返回真实节点函数 (已实现的) 或 stub (未实现的)。

    延迟导入: 让 deep graph 装配时不强依赖各专业 Agent 模块的 langchain/工具子树,
    没装 langchain 的 import 时机晚到节点首次执行。
    """
    if name == "metric_agent":
        from app.agents.metric_agent import run_metric_agent
        inner = run_metric_agent
    elif name == "log_agent":
        from app.agents.log_agent import run_log_agent
        inner = run_log_agent
    elif name == "infra_agent":
        from app.agents.infra_agent import run_infra_agent
        inner = run_infra_agent
    elif name == "runbook_agent":
        from app.agents.runbook_agent import run_runbook_agent
        inner = run_runbook_agent
    else:
        inner = _make_specialist_node(name, source, etype)
    # 套 dispatch_guard: EvidencePlan 没派遣的 Agent 直接跳过, 不调 LLM。
    return _dispatch_guard(name, inner)


def _stub_evidence(source: EvidenceSource, etype: str, summary: str) -> dict[str, Any]:
    """占位 Evidence (与 EvidenceCreate 字段对齐), 待专业 Agent 填真实内容。"""
    return {
        "source": str(source),
        "type": etype,
        "summary": summary,
        "content": {"stub": True},
        "score": None,
    }


# ============================================================
# ① IncidentManager —— 真节点 (M7 主线 1·步 6)
# ============================================================
async def incident_manager_node(state: DeepDiagnosisState) -> DeepDiagnosisState:
    """载入诊断对象 + 初始化 state。

    - worker 路径: state.task_id / incident_group_id / incident_id 都有 → 回查 DB 充实上下文;
    - 手动 SSE 路径: 这些字段为空, 跳过 DB 查 (无 task 事实行可查), 仅记 transition;
    - DB 异常: 降级, 不抛, 仅记 transition 详情。
    """
    task_id = state.get("task_id") or ""
    incident_group_id = state.get("incident_group_id") or ""

    if not task_id:
        # 手动诊断路径: 无 task 元信息, 直接放行 (不写 evidence, 让后续节点用 state.input)
        logger.info("[deep] IncidentManager: no task_id (manual SSE path)")
        return {
            "transition_history": [make_transition(
                "incident_manager", DEEP_INCIDENT_LOADED, "no task_id (manual path)",
            )],
        }

    detail = f"task={task_id}"
    try:
        # 延迟 import: 任何 DB 故障/无依赖都走降级
        from app.incidents.repository import incident_repository

        task = await incident_repository.get_task(task_id)
        if task is None:
            logger.warning(f"[deep] IncidentManager: task {task_id} not found in DB")
            return {
                "transition_history": [make_transition(
                    "incident_manager", DEEP_INCIDENT_LOADED, f"task {task_id} not found",
                )],
            }
        # 充实上下文: 把 DB task 关键字段透传 (alert_signature 已在 runner 里算好, 这里不重算)
        payload = task.get("payload") or {}
        patch: Dict[str, Any] = {
            "transition_history": [make_transition(
                "incident_manager", DEEP_INCIDENT_LOADED,
                f"{detail} alertname={payload.get('alertname', '-')} severity={payload.get('severity', '-')}",
            )],
        }
        # 如 state 没填 incident_group_id, 从 task 补上 (worker 路径已填; 双保险)
        if not incident_group_id and task.get("incident_group_id"):
            patch["incident_group_id"] = str(task["incident_group_id"])
        if not state.get("incident_id") and task.get("incident_id"):
            patch["incident_id"] = str(task["incident_id"])
        return patch
    except Exception as exc:
        # DB 故障降级: 不抛, deep graph 继续走
        logger.exception(f"[deep] IncidentManager DB 查询失败: {exc}")
        return {
            "transition_history": [make_transition(
                "incident_manager", DEEP_INCIDENT_LOADED,
                f"{detail} db_error: {type(exc).__name__}",
            )],
        }


# ============================================================
# ② CorrelationContext  —— 真节点 (M7 主线 1·步 6, C 的接入点之一)
# ============================================================
async def correlation_context_node(state: DeepDiagnosisState) -> DeepDiagnosisState:
    """构建关联上下文: 同组其它告警 (Postgres incident_groups) + LLM Wiki 经验召回。

    - 同 IncidentGroup 其它 alert 拉取 → 让 RCAJudge 知道本次不是孤立事件
    - LLM Wiki recall_block → 读 index 优先取相关历史经验页注入
    """
    incident_group_id = state.get("incident_group_id") or ""

    # LLM Wiki 召回: 读 index 优先取相关页作为一条 evidence 注入, 供 RCAJudge 参考。best-effort。
    lessons_evs = []
    try:
        from app.wiki.store import recall_block

        _block = await recall_block(
            query=str(state.get("input") or ""),
            signature=str(state.get("alert_signature") or ""),
        )
        if _block:
            lessons_evs.append({
                "source": str(EvidenceSource.INCIDENT_HISTORY),
                "type": "wiki_recall",
                "summary": ("LLM Wiki 召回: " + " / ".join(_block.splitlines()))[:200],
                "content": {"wiki": _block},
                "metadata": {"agent": "correlation_context", "kind": "wiki_recall"},
            })
    except Exception as _exc:
        logger.warning(f"[deep] wiki recall failed (ignored): {type(_exc).__name__}: {_exc}")

    if not incident_group_id:
        # 手动诊断路径: 无 group 元信息, 仅注入经验召回 (若有)
        logger.info("[deep] CorrelationContext: no incident_group_id (manual path)")
        return {
            "evidences": lessons_evs,
            "transition_history": [make_transition(
                "correlation_context", DEEP_CONTEXT_BUILT, "no group (manual path)",
            )],
        }

    try:
        from app.incidents.repository import incident_repository

        group = await incident_repository.get_incident_group(incident_group_id)
        if group is None:
            logger.warning(f"[deep] CorrelationContext: group {incident_group_id} not found")
            return {
                "transition_history": [make_transition(
                    "correlation_context", DEEP_CONTEXT_BUILT, f"group {incident_group_id} not found",
                )],
            }
        alert_count = int(group.get("alert_count") or 1)
        primary_service = str(group.get("primary_service") or "")
        severity = str(group.get("severity") or "")
        summary_text = str(group.get("summary") or "")[:200]

        summary = (
            f"本次告警属于 IncidentGroup `{incident_group_id}` "
            f"(共 {alert_count} 条同组告警; service=`{primary_service or '-'}`; "
            f"severity=`{severity or '-'}`)。group summary: {summary_text or '(无)'}"
        )

        ev = {
            "source": str(EvidenceSource.INCIDENT_HISTORY),
            "type": "incident_history",
            "summary": summary,
            "content": {
                "incident_group_id": incident_group_id,
                "alert_count": alert_count,
                "primary_service": primary_service,
                "severity": severity,
            },
            "metadata": {"agent": "correlation_context"},
        }
        logger.info(
            f"[deep] CorrelationContext: group={incident_group_id} alerts={alert_count}"
        )
        return {
            "evidences": [ev, *lessons_evs],
            "transition_history": [make_transition(
                "correlation_context", DEEP_CONTEXT_BUILT,
                f"group={incident_group_id} alerts={alert_count} svc={primary_service}",
            )],
        }
    except Exception as exc:
        logger.exception(f"[deep] CorrelationContext DB 查询失败: {exc}")
        # 降级: 不产 Evidence, 仅记 transition, deep graph 继续
        return {
            "transition_history": [make_transition(
                "correlation_context", DEEP_CONTEXT_BUILT, f"db_error: {type(exc).__name__}",
            )],
        }


# ============================================================
# ③ EvidencePlan —— 真节点 (M7 主线 1·步 5)
# ============================================================
# 设计取舍:
#   - 规则路由 (不上 LLM): 与 Reducer/Report 一致, 确定性优先, 少错少飘;
#     LLM 智能路由可作未来 v2 (signals 复杂到规则覆盖不够时再升)。
#   - LangGraph 的 fan-out 是图编译时定的 (4 条边永远在), 无法在 EvidencePlan
#     里动态裁剪。所以 EvidencePlan 只产 plan; 各专业 Agent 节点在被调用前
#     由 _resolve_specialist_node_fn 包一层 dispatch_guard, 不在派遣列表的
#     直接出 skipped transition + 空 evidences 返回, 不调 LLM 不产 Evidence。
#   - 默认组合 "metric+log": 信息密度最高的两类, 多数告警靠它们足以判定。

# 域关键词 → 派遣建议 (规则路由)。匹配多个域时取并集。
_PLAN_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    # (关键词模式, 应派出的 agents)
    ("cpu memory mem disk io load process 进程 内存 磁盘 负载 资源 cpu使用 卡顿 发热".split(),
     ("metric_agent",)),
    ("log 日志 error exception 报错 错误 异常 告警 alert 5xx 4xx 失败 traceback".split(),
     ("log_agent",)),
    ("docker container 容器 端口 port dns http 网络 network 依赖 服务不可达 connection refused timeout 超时 latency 慢请求 trace span 调用链 链路".split(),
     ("infra_agent", "log_agent")),
    ("sop runbook 手册 流程 规范 步骤 怎么处理 如何排查".split(),
     ("runbook_agent",)),
)

# "强信号" 关键词触发派出全部 (兜底覆盖)
_PLAN_BROADCAST_HINTS = ("全面诊断", "深度排查", "群聊", "全 agent", "全部 agent", "all agent", "broadcast")
# 默认派遣 (现象未匹配任何域时): metric + log 信息密度最高
_PLAN_DEFAULT_AGENTS = ("metric_agent", "log_agent")
# 所有可派 agents (集合, 顺序无所谓; 实际执行顺序由 fan-out 并发)
_PLAN_ALL_AGENTS = tuple(name for name, _, _ in SPECIALISTS)


def _route_by_keywords(text: str) -> tuple[list[str], str]:
    """规则路由: 现象文本 → 应派 agents + 策略标签 (供 transition 可观测)。"""
    import re

    def _hit(keyword: str) -> bool:
        if keyword.isascii() and keyword.replace("_", "").replace("-", "").isalnum():
            return re.search(rf"(?<![a-z0-9_-]){re.escape(keyword)}(?![a-z0-9_-])", norm) is not None
        return keyword in norm

    norm = (text or "").lower()
    if not norm.strip():
        return list(_PLAN_DEFAULT_AGENTS), "default_empty_input"
    # 强信号广播
    if any(h in norm for h in _PLAN_BROADCAST_HINTS):
        return list(_PLAN_ALL_AGENTS), "broadcast"
    hit_agents: list[str] = []
    for words, agents in _PLAN_KEYWORDS:
        if any(_hit(w) for w in words):
            for a in agents:
                if a not in hit_agents:
                    hit_agents.append(a)
    if not hit_agents:
        return list(_PLAN_DEFAULT_AGENTS), "default_no_match"
    return hit_agents, "keyword_match"


def evidence_plan_node(state: DeepDiagnosisState) -> DeepDiagnosisState:
    """识别故障域 → 决定派哪几个专业 subagent + 取证策略 (规则路由)。"""
    incident_text = state.get("input") or ""
    agents, strategy = _route_by_keywords(incident_text)
    plan = {"agents": agents, "strategy": strategy}
    logger.info(f"[deep] EvidencePlan: strategy={strategy} -> agents={agents}")
    return {
        "evidence_plan": plan,
        "transition_history": [make_transition(
            "evidence_plan", DEEP_EVIDENCE_PLANNED,
            f"strategy={strategy} agents=[{','.join(agents)}]",
        )],
    }


def _dispatch_guard(name: str, inner):
    """给专业 Agent 节点包一层: 如果 EvidencePlan 没派它, 直接 skip。

    skip 时: 产 1 条 "skipped" transition + 0 条 Evidence (空 patch),
    不调 LLM 不产 Evidence。Reducer/RCAJudge/Report 都做了"少证据"兜底。
    """
    import asyncio as _asyncio

    async def _async_wrapper(state: DeepDiagnosisState) -> DeepDiagnosisState:
        plan = state.get("evidence_plan") or {}
        agents = plan.get("agents") or list(_PLAN_ALL_AGENTS)  # 无 plan 时降级为全派
        if name not in agents:
            logger.info(f"[deep] {name} skipped (not in evidence_plan.agents={agents})")
            return {
                "transition_history": [make_transition(
                    name, DEEP_AGENT_DONE,
                    f"skipped (plan.strategy={plan.get('strategy', '-')})",
                )],
            }
        # 派遣中: 调真实节点
        if _asyncio.iscoroutinefunction(inner):
            return await inner(state)
        return inner(state)

    return _async_wrapper


# ============================================================
# ④ 专业 subagent (隔离上下文, 只回 Evidence) —— fan-out 并行
# ============================================================
def _make_specialist_node(name: str, source: EvidenceSource, etype: str):
    """造一个专业 subagent 节点 (stub)。

    真实实现 (TODO M7): 在这里启动一个**隔离的最小 agent 循环** ——
      - 自己的 scoped 输入 (现象 + evidence_plan 里给它的策略);
      - 自己的 LLM + 该域工具 (Log->日志工具, Metric->指标工具, ...);
      - 只把结论压成一条/几条 Evidence 返回, 中间推理不进共享 state。
    这就是课程 s06 的 subagent: 隔离 + 返回 summary, 而非 teammate 互聊。
    """

    def _node(state: DeepDiagnosisState) -> DeepDiagnosisState:
        logger.info(f"[deep] {name} (stub) -> {etype}")
        ev = _stub_evidence(source, etype, f"（stub）{name} 取证未实现")
        return {
            "evidences": [ev],
            "transition_history": [make_transition(name, DEEP_AGENT_DONE, f"stub: {etype}")],
        }

    return _node


# ============================================================
# ④' EvidenceReducer  (C 的接入点之二)
# ============================================================
# EvidenceReducer 确定性评分表 (M7 第一版, 不上 LLM)。
# 为什么这样定: metric 是"现场实测", 信息密度最高; infra 是运行环境/依赖现场证据,
# log/runbook 来自知识检索, incident_history 是辅证。
# error 证据 (metadata.error_type 非空) 不当根因候选 (score=0), 但仍计入 evidence_ids
# 供 RCAJudge / Report 看到"哪些工具/Agent 失败了"——失败信号本身也是诊断信息。
_EVIDENCE_BASE_SCORE: dict[str, float] = {
    "metric_snapshot": 1.0,
    "infra_snapshot": 0.90,
    "log_excerpt": 0.85,
    "runbook_match": 0.75,
    "incident_history": 0.60,
    # 兜底: 未见过的 type 给中等分, 不丢
    "_default": 0.50,
}

# 单个候选的 summary 截断 (在 candidate 字段里展示, 给 LLM/UI 用)
_CANDIDATE_TEXT_LIMIT = 240
# 输出最多多少个候选给下游 RCAJudge (限制 prompt 体量)
_CANDIDATES_TOP_K = 5


def _is_error_evidence(ev: dict[str, Any]) -> bool:
    """Evidence 是否标记为"产证 Agent 失败"。"""
    md = ev.get("metadata") or {}
    if md.get("error_type"):
        return True
    content = ev.get("content") or {}
    return bool(content.get("error"))


def _score_evidence(ev: dict[str, Any]) -> float:
    """按 Evidence type 打基础分; error 证据归零 (不当候选, 但保留链路)。"""
    if _is_error_evidence(ev):
        return 0.0
    etype = str(ev.get("type") or "")
    return _EVIDENCE_BASE_SCORE.get(etype, _EVIDENCE_BASE_SCORE["_default"])


def _ev_ref(idx: int) -> str:
    """生成对 state.evidences[idx] 的稳定引用。

    为什么不用真 DB id: deep graph 节点产的 Evidence 此时还是内存 dict, 真实 DB id
    要等 worker 路径的 runner.py 写库时才生成 (fast 路径同理)。所以这里先用列表
    下标作引用, 下游 ReportAgent 用 evidence_ids 反查 state.evidences[i] 即可;
    将来 M7 收尾把 Evidence 落库前后 id 映射统一时再升级。
    """
    return f"ev_{idx}"


async def evidence_reducer_node(state: DeepDiagnosisState) -> DeepDiagnosisState:
    """归并所有专业 Agent 产的 Evidence -> 输出候选根因列表。

    M7 确定性版 (不上 LLM, 少错少飘):
      1. 每条非 error Evidence 一个候选, summary 截断作 candidate 文本;
      2. 按 type 基础分排序 (metric > infra > log > runbook > incident_history);
      3. error Evidence 仍出现在每个候选的 evidence_ids 里 (供 RCAJudge 识别失败);
      4. paths 字段留空, 等待 M8/M9 KG 接入填充"证据路径"。

    TODO(M8/M9): 这里是 C(知识图谱) 的第二个接入点 —— 拿到 evidences 后调
      app/knowledge_graph/localizer.py 出"拓扑上游候选 + 证据路径", 与本节点的
      确定性候选合并/复核。当前先不依赖 KG, 让 deep 在 M7 阶段独立可跑。
    """
    evidences = state.get("evidences") or []
    if not evidences:
        logger.warning("[deep] EvidenceReducer: 无 Evidence, 产空候选")
        return {
            "candidates": [],
            "transition_history": [make_transition(
                "evidence_reducer", DEEP_EVIDENCE_REDUCED, "no evidence",
            )],
        }

    # 给每条 Evidence 分配稳定引用 (内存下标), 并打分
    scored: list[tuple[int, float, dict[str, Any]]] = []
    error_refs: list[str] = []
    for i, ev in enumerate(evidences):
        score = _score_evidence(ev)
        if _is_error_evidence(ev):
            error_refs.append(_ev_ref(i))
        scored.append((i, score, ev))

    # 候选 = 每条非 error Evidence; 按 score DESC, type 字典序 (稳定排序)
    candidates_all: list[dict[str, Any]] = []
    for i, score, ev in scored:
        if score <= 0:
            continue
        summary = str(ev.get("summary") or "").strip()
        if not summary:
            continue
        cand = {
            "candidate": summary[:_CANDIDATE_TEXT_LIMIT],
            "support_score": round(score, 3),
            "evidence_ids": [_ev_ref(i)] + error_refs,  # 本条 + 全部失败信号
            "source": str(ev.get("source") or ""),
            "type": str(ev.get("type") or ""),
        }
        # 透传 agent 元信息 (debug/可观测)
        agent = (ev.get("metadata") or {}).get("agent")
        if agent:
            cand["agent"] = agent
        candidates_all.append(cand)

    # 排序 + 截断 top_k
    candidates_all.sort(key=lambda c: (-c["support_score"], c["type"]))
    candidates = candidates_all[:_CANDIDATES_TOP_K]

    logger.info(
        f"[deep] EvidenceReducer: 收到 {len(evidences)} 条 Evidence (error={len(error_refs)}), "
        f"得 {len(candidates)} 候选"
    )
    return {
        "candidates": candidates,
        "transition_history": [make_transition(
            "evidence_reducer",
            DEEP_EVIDENCE_REDUCED,
            f"evidences={len(evidences)} errors={len(error_refs)} candidates={len(candidates)}",
        )],
    }


# ============================================================
# ⑤ RCAJudge —— 真节点 (M7 主线 1·步 3)
# ============================================================
# RCAJudge 的契约 (SSOT §4.5):
#   - 只看结构化证据 (candidates + 关键 evidences 的 summary), **不读 content 原文**;
#   - LLM 排序候选 + 写一段判定理由, 输出 rca 字段 + 一条 rca 类型 Evidence;
#   - 不调工具, 只调 LLM 一次, 解析失败降级到 candidates[0]。
# 设计取舍:
#   - 直接在 graph 文件内, 不另开 rca_judge_agent.py —— RCAJudge 不是 s06 隔离 subagent
#     (没工具循环), 与节点逻辑紧密耦合, 不抽出去。
#   - 用 harness.report_model() (相比 executor_model 更强), 判断质量优先。

_RCA_SYSTEM_PROMPT = (
    "你是 SRE 根因判定法官 (RCA Judge)。下面给你一组**候选根因** (已按确定性算法初排序) 和"
    "一组**关键证据 summary** (来自多个专业 Agent 的观察结论)。\n"
    "你的职责: ① 对候选**重新排序**, 把最可能的根因排第一; ② 写一段≤200 字的中文判定理由;"
    "③ 列出最关键的 3-5 个支持证据 (按 evidence_id, 取 evidence_ids 字段里的引用)。\n\n"
    "硬性约束:\n"
    "1. **只看本 prompt 给的 summary, 不要假设你看过原始日志/指标/调用链**;\n"
    "2. 优先看 metric 类证据 (现场实测), 次看 infra (运行环境/依赖), 再看 log/runbook 和 incident_history;\n"
    "3. 如果有标记 error 的证据, 说明对应 Agent 失败, 在 reasoning 里点明这部分信息缺失;\n"
    "4. 只输出一个 JSON 对象, 不要任何解释或 markdown 围栏。字段:\n"
    "   {\n"
    '     "root_cause": "<一句话最可能根因>",\n'
    '     "ranked_candidates": ["<按可能性降序的 candidate 文本列表>"],\n'
    '     "supporting_evidence_ids": ["ev_X", ...],\n'
    '     "reasoning": "<判定理由 (中文, ≤200 字)>",\n'
    '     "confidence": <0.0-1.0>\n'
    "   }"
)


def _build_rca_user_prompt(candidates: list[dict[str, Any]], evidences: list[dict[str, Any]]) -> str:
    """组装 RCAJudge 的 user prompt: 候选 + evidence summary 表 (不带 content 原文)。"""
    lines: list[str] = ["候选根因 (确定性初排):"]
    for i, c in enumerate(candidates):
        lines.append(
            f"  C{i}: score={c.get('support_score', 0):.2f} type={c.get('type', '')} "
            f"agent={c.get('agent', '-')}\n"
            f"     candidate: {c.get('candidate', '')[:200]}\n"
            f"     evidence_ids: {c.get('evidence_ids', [])}"
        )
    lines.append("")
    lines.append("关键证据 summary (按 ev_i 引用; 不展示 content 原文):")
    for i, ev in enumerate(evidences):
        is_err = bool((ev.get("metadata") or {}).get("error_type") or (ev.get("content") or {}).get("error"))
        marker = " [ERROR]" if is_err else ""
        lines.append(
            f"  ev_{i}{marker}: source={ev.get('source', '')} type={ev.get('type', '')}\n"
            f"     summary: {str(ev.get('summary') or '')[:200]}"
        )
    lines.append("")
    lines.append("请按系统约束输出 JSON。")
    return "\n".join(lines)


def _parse_rca_json(text: str) -> dict[str, Any]:
    """从 LLM 输出抠 JSON; 失败抛异常交给降级路径。"""
    import json
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw[:4].lower() == "json":
            raw = raw[4:]
    s, e = raw.find("{"), raw.rfind("}")
    if s == -1 or e <= s:
        raise ValueError("no json object in rca output")
    obj = json.loads(raw[s : e + 1])
    if not isinstance(obj, dict):
        raise ValueError("rca output is not a json object")
    return obj


def _rca_fallback(candidates: list[dict[str, Any]], reason: str) -> dict[str, Any]:
    """LLM 不可用 / 解析失败时的确定性兜底: 取 Reducer 已排序的 candidates[0]。"""
    top = candidates[0] if candidates else {}
    return {
        "root_cause": str(top.get("candidate") or "(无候选可定)"),
        "ranked_candidates": [c.get("candidate", "") for c in candidates],
        "supporting_evidence_ids": list(top.get("evidence_ids") or []),
        "reasoning": f"(确定性兜底: {reason}; 取 Reducer 评分最高候选)",
        "confidence": float(top.get("support_score") or 0.0),
        "via": "fallback",
    }


async def rca_judge_node(state: DeepDiagnosisState) -> DeepDiagnosisState:
    """RCAJudge 真节点: LLM 看 candidates + evidence summary 排序定根因。"""
    candidates = state.get("candidates") or []
    evidences = state.get("evidences") or []

    if not candidates:
        logger.warning("[deep] RCAJudge: 无候选, 跳过")
        rca = {"root_cause": "(无候选)", "ranked_candidates": [], "supporting_evidence_ids": [],
               "reasoning": "EvidenceReducer 未产候选 (可能所有 Evidence 都标 error)", "confidence": 0.0,
               "via": "empty"}
        return {
            "rca": rca,
            "evidences": [_rca_evidence(rca)],
            "transition_history": [make_transition("rca_judge", DEEP_RCA_JUDGED, "no candidates")],
        }

    via = "llm"
    try:
        # 延迟 import: LLM / harness 缺失走降级
        from app.core.llm import get_chat_llm
        from app.runtime.agent_harness import get_agent_harness

        harness = get_agent_harness()
        llm = get_chat_llm(
            model=harness.report_model(),   # 用 report_model (相比 executor_model 更强, 判断优先)
            temperature=0,
            streaming=False,
        )
        resp = await llm.ainvoke([
            ("system", _RCA_SYSTEM_PROMPT),
            ("human", _build_rca_user_prompt(candidates, evidences)),
        ])
        raw = getattr(resp, "content", "") or ""
        text = raw if isinstance(raw, str) else str(raw)
        parsed = _parse_rca_json(text)

        # 字段归一化 + 兜底
        rca = {
            "root_cause": str(parsed.get("root_cause") or "")[:500] or candidates[0].get("candidate", ""),
            "ranked_candidates": list(parsed.get("ranked_candidates") or [c.get("candidate", "") for c in candidates]),
            "supporting_evidence_ids": list(parsed.get("supporting_evidence_ids") or candidates[0].get("evidence_ids") or []),
            "reasoning": str(parsed.get("reasoning") or "")[:600],
            "confidence": float(parsed.get("confidence") or candidates[0].get("support_score") or 0.0),
            "via": via,
        }
        logger.info(f"[deep] RCAJudge: root_cause={rca['root_cause'][:60]!r} conf={rca['confidence']}")
    except Exception as exc:
        logger.exception(f"[deep] RCAJudge LLM failed, fallback: {exc}")
        via = "fallback"
        rca = _rca_fallback(candidates, f"{type(exc).__name__}")

    return {
        "rca": rca,
        "evidences": [_rca_evidence(rca)],
        "transition_history": [make_transition("rca_judge", DEEP_RCA_JUDGED, f"via={via} conf={rca['confidence']:.2f}")],
    }


def _rca_evidence(rca: dict[str, Any]) -> dict[str, Any]:
    """把 RCAJudge 的判定结果包成一条 rca 类型 Evidence (ReportAgent 也能拿到)。"""
    return {
        "source": str(EvidenceSource.RCA),
        "type": "rca",
        "summary": str(rca.get("root_cause") or "")[:500],
        "content": {"rca": rca},
        "metadata": {"agent": "rca_judge", "via": rca.get("via", "")},
    }


# ============================================================
# ⑥ RemediationPlanner —— 真节点 (M7 主线 1·步 6)
# ============================================================
# 设计取舍:
#   - 确定性 + 可选 LLM 增强 (本节点保守: 先纯确定性, 让 ReportAgent 拿到结构化步骤);
#   - 步骤分两类:
#     a) "诊断验证类" (只读, 无副作用) - 默认推荐执行;
#     b) "处置写操作类" (重启/扩容/限流) - 必须 requires_human_confirm=True;
#   - 不实际执行任何写操作 (§6 不做全自动修复约束)。

# 基于 rca.root_cause / candidates.type 的规则模板。
# 顺序敏感: 命中即返回, 故"具体技术"(redis/mysql) 必须排在"通用症状"(latency/log) 之前 ——
# 否则 "MySQL 慢查询" 会被 latency 模板的 "慢" 截胡。
_REMEDIATION_TEMPLATES: tuple[tuple[tuple[str, ...], list[str], list[str]], ...] = (
    # === 具体技术优先 ===
    (("redis", "缓存"),
     ["复核 Redis 命中率 + 大 key", "查看主从复制延迟"],
     ["清理大 key", "扩容 Redis / 读写分离"]),
    (("mysql", "数据库", "db", "慢查询"),
     ["查慢查询日志", "检查活跃连接数 + 锁等待"],
     ["kill 长事务", "评估读库扩容"]),
    # === 资源症状 ===
    (("cpu", "load", "进程", "process", "占用", "卡顿"),
     ["复核 top CPU 进程是否预期内", "对比历史基线确认是否阈值偏低"],
     ["限流/降级该服务的非关键请求", "评估扩容 worker / 实例"]),
    (("memory", "mem", "内存", "oom"),
     ["列出 top 内存进程 + RSS", "检查是否有内存泄漏迹象 (持续增长)"],
     ["重启占用最高的进程 (业务停机窗口内)", "评估扩容内存或开 swap"]),
    (("disk", "磁盘", "inode", "no space"),
     ["列出大文件 (du -sh)", "检查日志轮转 / 临时文件"],
     ["清理过期日志/临时文件", "扩容磁盘"]),
    # === 通用症状 (兜底, 排最后) ===
    (("latency", "timeout", "超时", "慢"),
     ["拉取 P95/P99 趋势确认", "检查依赖服务健康度"],
     ["熔断/降级慢依赖", "扩容并发能力"]),
    (("log", "5xx", "error", "exception", "异常"),
     ["按命中模板的关键字过滤近 1 小时日志样本", "确认是否新版本上线后开始 (变更关联)"],
     ["回滚最近变更", "联系上游服务确认依赖"]),
)


def _match_remediation(rca_text: str, candidates: list[dict[str, Any]]) -> tuple[list[str], list[str], str]:
    """规则匹配处置模板: 优先看 rca.root_cause, 兜底看 candidates.candidate 文本。"""
    combined = (rca_text or "").lower()
    for c in candidates[:3]:
        combined += " " + str(c.get("candidate") or "").lower()

    for keywords, readonly_steps, writeop_steps in _REMEDIATION_TEMPLATES:
        if any(k in combined for k in keywords):
            return readonly_steps, writeop_steps, ",".join(keywords[:2])
    # 兜底: 通用建议
    return (
        ["调取关键 metric 趋势 (CPU/Mem/Latency/QPS) 复核", "查最近 1 小时变更/发布记录"],
        ["如确认影响面, 优先回滚最近变更"],
        "default",
    )


def remediation_planner_node(state: DeepDiagnosisState) -> DeepDiagnosisState:
    """RemediationPlanner 真节点: 据 rca 出处置建议; 写操作必须人工确认。"""
    rca = state.get("rca") or {}
    candidates = state.get("candidates") or []
    root_cause = str(rca.get("root_cause") or "")

    readonly_steps, writeop_steps, matched = _match_remediation(root_cause, candidates)

    # 合并 + 标注步骤类型
    steps: list[str] = []
    for s in readonly_steps:
        steps.append(f"[只读] {s}")
    for s in writeop_steps:
        steps.append(f"[写操作·需人工] {s}")

    remediation = {
        "steps": steps,
        "requires_human_confirm": True,    # 任何写操作都必须 True (§6 约束)
        "matched_template": matched,
        "based_on_rca_via": str(rca.get("via") or ""),
    }
    logger.info(
        f"[deep] RemediationPlanner: matched={matched} steps={len(steps)} "
        f"(readonly={len(readonly_steps)} writeop={len(writeop_steps)})"
    )
    return {
        "remediation": remediation,
        "transition_history": [make_transition(
            "remediation_planner", DEEP_REMEDIATION_PLANNED,
            f"matched={matched} steps={len(steps)}",
        )],
    }


# ============================================================
# ⑦ ReportAgent —— 真节点 (M7 主线 1·步 4)
# ============================================================
# 设计取舍:
#   - 不调 LLM —— RCAJudge 已做完判断 (rca.reasoning 是现成中文文本), Report 就是把
#     判断结果格式化。再调 LLM 增加成本/不确定性, 无明显收益。
#   - 引用形态用 ev_i (与 EvidenceReducer 的 _ev_ref 同源, 形成完整链路): 报告里
#     "[ev_0]" 对应 state.evidences[0]; M7 收尾把内存 ev_i 映射到真实 DB id 时
#     报告也会自动指向真 id (只需替换 _ev_ref 实现)。
#   - response 字段触发图 END; diagnosis_runner 的 _convert_node_event 已接好,
#     SSE 会发 type=report 事件 (与 fast 同款), 前端零改动复用。
#   - cache_reports 由 runner 控制 (worker=False, SSE=True), 这里不管。


def _fmt_evidence_line(idx: int, ev: dict[str, Any]) -> str:
    """渲染证据链中的一行 (引用形如 [ev_3])。"""
    agent = (ev.get("metadata") or {}).get("agent") or "-"
    is_err = bool((ev.get("metadata") or {}).get("error_type") or (ev.get("content") or {}).get("error"))
    marker = " **[ERROR]**" if is_err else ""
    summary = str(ev.get("summary") or "").strip().replace("\n", " ")
    return (
        f"- `[{_ev_ref(idx)}]`{marker} `{ev.get('source', '')}/{ev.get('type', '')}` "
        f"by `{agent}` — {summary[:240]}"
    )


def _fmt_candidate_line(rank: int, cand: dict[str, Any]) -> str:
    return (
        f"{rank}. `{cand.get('type', '')}` (score={cand.get('support_score', 0):.2f}, "
        f"by {cand.get('agent', '-')}, refs={cand.get('evidence_ids', [])}): "
        f"{cand.get('candidate', '')[:200]}"
    )


def _fmt_remediation(rem: dict[str, Any]) -> str:
    """处置建议块: 写操作必须人工确认 (§5 M7 DoD 契约)。"""
    if not rem:
        return "_(RemediationPlanner 未运行或未产建议)_"
    steps = rem.get("steps") or []
    need_human = rem.get("requires_human_confirm", True)
    head = "⚠️ **以下处置含写操作, 需人工确认后执行**\n" if need_human else ""
    if not steps:
        return head + "_(暂无具体处置步骤)_"
    return head + "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))


def report_node(state: DeepDiagnosisState) -> DeepDiagnosisState:
    """ReportAgent 真节点: 把 rca / candidates / evidences / remediation 渲染成 Markdown。

    填入 state.response 后 LangGraph 自动到 END; SSE 会把 response 发为 type=report 事件。
    """
    incident_text = state.get("input") or ""
    task_id = state.get("task_id") or ""
    incident_group_id = state.get("incident_group_id") or ""
    alert_signature = state.get("alert_signature") or ""
    rca = state.get("rca") or {}
    candidates = state.get("candidates") or []
    evidences = state.get("evidences") or []
    remediation = state.get("remediation") or {}

    # 统计 agent 阵亡
    agents_failed = []
    agents_ok = []
    for ev in evidences:
        agent = (ev.get("metadata") or {}).get("agent") or ""
        if not agent or agent == "rca_judge":
            continue
        if (ev.get("metadata") or {}).get("error_type") or (ev.get("content") or {}).get("error"):
            if agent not in agents_failed:
                agents_failed.append(agent)
        else:
            if agent not in agents_ok:
                agents_ok.append(agent)

    via = str(rca.get("via") or "")
    confidence = float(rca.get("confidence") or 0.0)
    root_cause = str(rca.get("root_cause") or "(未判定)")
    reasoning = str(rca.get("reasoning") or "_(无判定理由)_")

    parts: list[str] = []
    parts.append("# 深度诊断报告 (Deep Diagnosis Report)")
    parts.append("")

    # 现象
    parts.append("## 现象")
    parts.append(incident_text or "_(未提供现象描述)_")
    parts.append("")

    # 根因判定
    parts.append("## 根因判定")
    parts.append(f"- **最可能根因**: {root_cause}")
    parts.append(f"- **置信度**: {confidence:.2f}")
    parts.append(f"- **判定来源**: `{via or 'unknown'}`")
    sup = rca.get("supporting_evidence_ids") or []
    if sup:
        parts.append(f"- **关键支持证据**: {', '.join(f'`{e}`' for e in sup)}")
    parts.append("")
    parts.append("**判定理由**: " + reasoning)
    parts.append("")

    # 候选根因 (RCAJudge 排序)
    if candidates:
        parts.append("## 候选根因 (按可能性排序)")
        for i, c in enumerate(candidates):
            parts.append(_fmt_candidate_line(i + 1, c))
        parts.append("")

    # 证据链
    if evidences:
        parts.append(f"## 证据链 (共 {len(evidences)} 条)")
        for i, ev in enumerate(evidences):
            parts.append(_fmt_evidence_line(i, ev))
        parts.append("")

    # 处置建议
    parts.append("## 处置建议")
    parts.append(_fmt_remediation(remediation))
    parts.append("")

    # 元数据
    parts.append("---")
    parts.append("### 元数据")
    parts.append(f"- task_id: `{task_id or '-'}`")
    parts.append(f"- incident_group_id: `{incident_group_id or '-'}`")
    parts.append(f"- alert_signature: `{alert_signature or '-'}`")
    parts.append(f"- 产证成功 Agent: {', '.join(f'`{a}`' for a in agents_ok) or '_(无)_'}")
    if agents_failed:
        parts.append(f"- 产证失败 Agent: {', '.join(f'`{a}`' for a in agents_failed)} ⚠️")
    parts.append("- 诊断模式: `deep` (独立诊断图)")

    response = "\n".join(parts)
    logger.info(
        f"[deep] ReportAgent: rendered {len(response)} 字, evidences={len(evidences)} "
        f"candidates={len(candidates)} rca.via={via} failed_agents={len(agents_failed)}"
    )
    return {
        "response": response,
        "transition_history": [make_transition(
            "report", DEEP_REPORT_DONE,
            f"len={len(response)} evidences={len(evidences)} via={via}",
        )],
    }


def build_deep_graph():
    """构建 Deep Diagnosis 图。

    Returns:
        编译后的 CompiledStateGraph。
    """
    wf = StateGraph(DeepDiagnosisState)

    # 节点
    wf.add_node("incident_manager", incident_manager_node)
    wf.add_node("correlation_context", correlation_context_node)
    wf.add_node("evidence_plan", evidence_plan_node)
    for name, source, etype in SPECIALISTS:
        wf.add_node(name, _resolve_specialist_node_fn(name, source, etype))
    wf.add_node("evidence_reducer", evidence_reducer_node)
    wf.add_node("rca_judge", rca_judge_node)
    wf.add_node("remediation_planner", remediation_planner_node)
    wf.add_node("report", report_node)

    # 边: 串行前段
    wf.add_edge(START, "incident_manager")
    wf.add_edge("incident_manager", "correlation_context")
    wf.add_edge("correlation_context", "evidence_plan")
    # fan-out (并行专业 subagent) + fan-in (多入边 -> evidence_reducer 自动作 join barrier)
    for name, _, _ in SPECIALISTS:
        wf.add_edge("evidence_plan", name)
        wf.add_edge(name, "evidence_reducer")
    # 串行后段
    wf.add_edge("evidence_reducer", "rca_judge")
    wf.add_edge("rca_judge", "remediation_planner")
    wf.add_edge("remediation_planner", "report")
    wf.add_edge("report", END)

    compiled = wf.compile()
    logger.info(
        "[deep] Deep Diagnosis graph 已编译: "
        f"IncidentManager->CorrelationContext->EvidencePlan->[{len(SPECIALISTS)} 专业 Agent 并行]"
        "->EvidenceReducer->RCAJudge->RemediationPlanner->Report"
    )
    return compiled
