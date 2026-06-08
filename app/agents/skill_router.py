from __future__ import annotations

from loguru import logger
from pydantic import BaseModel, Field

from app.agents.state import PlanExecuteState
from app.core.llm import get_chat_llm
from app.core.structured import ainvoke_structured
from app.wiki.store import recall_block
from app.runtime.agent_harness import get_agent_harness
from app.runtime.transitions import (
    ROUTER_FALLBACK_GENERIC,
    ROUTER_LLM_FAILED,
    ROUTER_OK,
    ROUTER_OUT_OF_SCOPE,
    ROUTER_RECALL_APPLIED,
    make_transition,
)
from app.skills.registry import GENERIC_SKILL_NAME, get_skill_registry


class SkillChoice(BaseModel):
    is_oncall: bool = Field(default=True, description="用户输入是否属于 OnCall/运维诊断范围")
    skill_name: str = Field(..., description="选中的 Skill name (snake_case), 必须是给定菜单中已存在的项")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="路由置信度, 0 到 1")
    reason: str = Field(default="", description="一句话说明为什么选这个 Skill, 用于可观测")


_ONCALL_KEYWORDS = (
    "告警", "故障", "异常", "报错", "错误", "打不开", "打不开了", "无法打开", "无法访问",
    "访问不了", "访问失败", "宕机", "挂了", "挂掉", "白屏", "黑屏", "空白页", "不可用",
    "没反应", "请求失败", "加载失败", "登录失败", "支付失败", "超时", "延迟", "慢", "卡顿",
    "连接", "断开", "重启", "崩溃", "排查", "诊断", "根因", "事故", "复盘", "发布",
    "变更", "回滚", "扩容", "限流", "降级", "日志", "监控", "指标", "服务", "页面", "网站",
    "网页", "前端", "后端", "应用", "系统", "业务", "用户", "客户", "接口", "数据库", "缓存",
    "队列", "内存", "磁盘", "负载", "流量", "cpu", "memory", "disk", "load", "oom", "error",
    "exception", "timeout", "latency", "redis", "mysql", "mongodb", "mongo", "kafka", "etcd", "nginx",
    "jvm", "gc", "pod", "k8s", "kubernetes", "prometheus", "jaeger", "trace", "slo", "http", "rpc",
    "5xx", "4xx", "qps", "inode", "我电脑", "我的电脑", "我笔记本", "我的笔记本", "本机",
    "这台电脑", "这台机器", "自己的电脑", "我的机器", "本地电脑", "本地机器", "localhost",
    "my computer", "my laptop", "my pc",
)

_OUT_OF_SCOPE_KEYWORDS = (
    "动漫", "漫画", "电影", "电视剧", "小说", "游戏", "天气", "旅游", "美食", "菜谱", "星座", "八卦",
)

_AMBIGUOUS_INCIDENT_HINTS = (
    "打不开", "无法打开", "无法访问", "访问不了", "挂了", "白屏", "黑屏", "没反应", "失败", "慢", "卡",
)


def _looks_like_oncall_input(text: str) -> bool:
    normalized = (text or "").lower()
    if any(keyword in normalized for keyword in _OUT_OF_SCOPE_KEYWORDS):
        return False
    if any(keyword in normalized for keyword in _AMBIGUOUS_INCIDENT_HINTS):
        return True
    return any(keyword in normalized for keyword in _ONCALL_KEYWORDS)


def _build_out_of_scope_response(user_input: str) -> str:
    return (
        "# 无法启动 OnCall 诊断\n\n"
        f"你输入的内容是：`{user_input.strip() or '(空)'}`。\n\n"
        "它看起来不是运维告警、故障现象、监控指标异常、日志异常、发布变更或系统稳定性问题，"
        "因此我没有继续调用知识库、监控工具或日志工具。\n\n"
        "如果你想进行故障诊断，请补充类似下面的信息：\n\n"
        "- **服务/实例**：例如 `redis-master-01`、`web-api`、`mysql-master-01`\n"
        "- **异常现象**：例如 CPU 高、内存 98%、5xx 升高、连接超时、Pod 重启\n"
        "- **持续时间**：例如持续 10 分钟、最近 1 小时\n"
        "- **影响范围**：例如部分用户失败、核心接口不可用、客户端连接被断开"
    )


def _build_router_fallback_result(user_input: str) -> PlanExecuteState:
    if not _looks_like_oncall_input(user_input):
        reason = "Router LLM 调用失败后, 规则兜底判断为非 OnCall 输入"
        logger.info(f"[Router] fallback 非 OnCall 输入, 直接结束: {user_input[:100]!r}")
        return {
            "selected_skill": GENERIC_SKILL_NAME,
            "skill_reason": reason,
            "plan": [],
            "response": _build_out_of_scope_response(user_input),
            "iteration": 0,
        }
    return {
        "selected_skill": GENERIC_SKILL_NAME,
        "skill_reason": "Router LLM 调用失败后, 规则兜底放行到 generic_oncall",
    }


async def skill_router_node(state: PlanExecuteState) -> PlanExecuteState:
    user_input = state.get("input", "")
    registry = get_skill_registry()
    available = registry.names()

    if not available:
        logger.warning("[Router] SkillRegistry 为空, 跳过路由")
        return {"selected_skill": "", "skill_reason": "registry empty"}

    non_generic = [n for n in available if n != GENERIC_SKILL_NAME]
    if not non_generic:
        logger.info("[Router] 仅有兜底 Skill, 直接选择 generic_oncall")
        return {
            "selected_skill": GENERIC_SKILL_NAME,
            "skill_reason": "no specific skill defined, fallback to generic",
        }

    harness = get_agent_harness()
    router_model = harness.router_model()
    llm = get_chat_llm(model=router_model, temperature=0, timeout=30, max_retries=1)
    # 经验回灌: 从 LLM Wiki 召回相关页注入 router prompt (read-index-first, best-effort)。
    lessons = await recall_block(
        query=user_input, signature=str(state.get("alert_signature") or ""),
    )
    # 回灌可观测性: 命中时记一条 transition, 让"用没用回灌、注入了几页"进结构化事件流
    # (diagnosis_runner 会把 transition_history 转成 transition 事件)。无命中则 None。
    recall_count = sum(1 for ln in lessons.splitlines() if ln.startswith("### ")) if lessons else 0
    recall_transition = (
        make_transition("skill_router", ROUTER_RECALL_APPLIED, f"注入 {recall_count} 个相关 wiki 页")
        if recall_count
        else None
    )
    messages = harness.build_skill_router_messages(
        menu=registry.to_router_menu(),
        user_input=user_input,
        generic=GENERIC_SKILL_NAME,
        lessons=lessons,
    )

    try:
        choice = await ainvoke_structured(
            llm=llm,
            schema_cls=SkillChoice,
            messages=messages,
            model_name=router_model,
        )
    except Exception as e:
        detail = f"{type(e).__name__}: {e}"
        logger.exception(f"[Router] LLM 路由失败, 使用规则兜底: {e}")
        logger.warning(f"[transition] node=skill_router reason={ROUTER_LLM_FAILED} detail={detail}")
        result = _build_router_fallback_result(user_input)
        result["transition_history"] = (
            [recall_transition] if recall_transition else []
        ) + [make_transition("skill_router", ROUTER_LLM_FAILED, detail)]
        return result

    if not choice.is_oncall:
        reason = choice.reason or "Router 判断输入不属于 OnCall/运维诊断范围"
        logger.info(
            f"[Router] LLM 判断非 OnCall, 直接结束: confidence={choice.confidence}, input={user_input[:100]!r}"
        )
        logger.info(f"[transition] node=skill_router reason={ROUTER_OUT_OF_SCOPE}")
        return {
            "selected_skill": GENERIC_SKILL_NAME,
            "skill_reason": reason,
            "plan": [],
            "response": _build_out_of_scope_response(user_input),
            "iteration": 0,
            "transition_history": (
                [recall_transition] if recall_transition else []
            ) + [make_transition("skill_router", ROUTER_OUT_OF_SCOPE, reason)],
        }

    chosen = choice.skill_name.strip().lower()
    fallback_used = False
    if chosen not in available:
        logger.warning(f"[Router] LLM 返回不存在的 skill {chosen!r}, 回退到 {GENERIC_SKILL_NAME}")
        logger.warning(f"[transition] node=skill_router reason={ROUTER_FALLBACK_GENERIC} unknown={chosen!r}")
        unknown = chosen
        chosen = GENERIC_SKILL_NAME
        fallback_used = True

    skill = registry.get(chosen)
    display = skill.display_name if skill else chosen
    logger.info(
        f"[Router] 选择 Skill: {chosen} ({display}) | confidence={choice.confidence} | reason={choice.reason}"
    )

    if fallback_used:
        transition = make_transition(
            "skill_router",
            ROUTER_FALLBACK_GENERIC,
            f"LLM 返回未知 skill={unknown!r}, 回退到 {GENERIC_SKILL_NAME}",
        )
    else:
        transition = make_transition(
            "skill_router",
            ROUTER_OK,
            f"chosen={chosen} confidence={choice.confidence}",
        )
    return {
        "selected_skill": chosen,
        "skill_reason": choice.reason,
        "transition_history": (
            [recall_transition] if recall_transition else []
        ) + [transition],
    }
