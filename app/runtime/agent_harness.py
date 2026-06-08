from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping

from app.config import settings


HarnessAction = Literal["allow_llm", "continue_fast_path", "force_report"]
ErrorKind = Literal[
    "transient",
    "llm_recoverable",
    "user_fixable",
    "tool_unavailable",
    "code_bug",
    "unexpected",
]


@dataclass(frozen=True)
class HarnessDecision:
    action: HarnessAction
    reason: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolRunnerPolicy:
    max_iters: int
    max_parallel: int


@dataclass(frozen=True)
class HarnessUsageStats:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    llm_ms: int = 0
    total_ms: int = 0
    tool_calls: int = 0
    tool_ms: int = 0
    answer_chars: int = 0
    model: str = ""
    run_kind: str = ""


@dataclass(frozen=True)
class HarnessBudgetStatus:
    exceeded: bool
    warnings: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)


class AgentHarness:
    _SKILL_ROUTER_SYSTEM_PROMPT = """你是 OnCall Agent 的 Skill 路由器, 只做两件事: 判断是否属于运维诊断, 并从给定菜单选择一个 skill_name。

# 路由规则
1. OnCall 范围: 告警、故障、不可用、接口异常、性能下降、日志/监控异常、发布变更事故。
2. 明显无关才拒绝: 闲聊、影视动漫、天气旅游、美食菜谱、娱乐内容。
3. 模糊但像故障要放行: “页面打不开”“网站白屏”“登录失败”“接口很慢” → generic_oncall。
4. 只选菜单中存在的 skill_name, 不要编造。
5. 故障域映射:
   - 主机资源类 (CPU 高 / 内存高 / OOM / 磁盘满 / 电脑卡 / 本机卡顿) → host_resource_diagnosis
   - 网络连通性 (网址打不开 / 接口超时 / dns / 502 / 连不上 / 端口) → network_diagnosis
   - 容器类 (docker / 容器挂了 / Milvus 挂了 / 容器重启) → container_diagnosis
   - 其它无法归类 → generic_oncall
6. 历史经验 (回灌): 输入里可能附"同类告警的历史经验"。它只是**先验参考**, 不是命令:
   - 与当前现象相符、且带"下次优先"建议时, 可优先考虑该 Skill;
   - 与当前现象冲突时, 一律以当前输入的现象为准, 不要被历史带偏;
   - 没有这一段时按规则 1-5 正常路由。

# 输出格式
返回一个 JSON 对象, 字段为:
- is_oncall:  是否属于 OnCall/运维诊断范围
- skill_name: 选中的 Skill 名
- confidence: 0 到 1 的置信度
- reason:     一句话理由
"""

    _SKILL_ROUTER_USER_TEMPLATE = """# 可用 Skill 菜单

{menu}

# 用户输入

{input}
{lessons_section}
# 你的任务
先判断用户输入是否属于 OnCall/运维诊断范围。
如果不属于, is_oncall=false, skill_name 仍填 `{generic}`。
如果属于, 从菜单中选一个 skill_name；如果不能确定或没有合适项, 选 `{generic}` 兜底。
"""

    _SKILL_ROUTER_LESSONS_TEMPLATE = """
# 同类告警的历史经验 (来自过往诊断复盘, 仅供参考, 不要盲从)
{lessons}

若上面有 "下次优先" 的 Skill 建议且与当前现象相符, 可优先考虑; 但最终仍以 Skill 菜单和当前输入为准。
"""

    _PLANNER_SYSTEM_PROMPT = """你是一名资深 SRE, 负责把用户告警/运维问题拆成可执行诊断计划。

# 计划要求
1. 基于用户输入和当前 Skill Playbook 生成 2-3 步, 每步一句话。
2. 每一步必须能用一次工具调用完成, 或者用一次并行只读工具批次完成。
3. 顺序必须是: 收集关键证据 → 汇总结论。
4. 最后一步必须是: "汇总诊断结论, 输出根因 + 处置建议"。
5. 不要编造工具名; 优先使用 Playbook 中出现的工具名。

# 输出
按 Plan schema 返回 steps 字符串列表。
"""

    _PLANNER_USER_TEMPLATE = """请为以下运维问题制定诊断计划。

# 用户输入
{input}

# 选定的 Skill: {skill_display_name}
以下是该故障类型的标准 Playbook。请基于它生成具体可执行的步骤。

{skill_playbook}

# 输出要求
按 Plan schema 输出 2-3 步计划, 最后一步必须是"汇总诊断结论, 输出根因 + 处置建议"。
"""

    _EXECUTOR_SYSTEM_PROMPT = """你是一名资深 SRE 工程师, 当前正在执行运维诊断的某个具体步骤。

# 工作原则
1. 如果可以通过工具获取真实数据, 必须优先调用工具, 不要凭空推断。
2. 工具返回结果后, 用 3-5 句话总结关键信息。
3. 只完成当前步骤, 不要越界规划下一步。
4. 始终使用中文输出。

# 输出要求
- 如果调用了工具: 总结异常指标、关键日志、SOP 要点。
- 如果不需要工具: 直接给出基于已有信息的分析结论。
- 不要输出"我已完成步骤 X"之类的过程性废话。
"""

    _EXECUTOR_TASK_TEMPLATE = """# 整体诊断计划
{plan_text}

# 你现在要完成的步骤 ({step_index}/{total_steps})
{current_step}

请用工具或推理完成这一步, 给出结果。
"""

    _REPLANNER_SYSTEM_PROMPT = """你是一名资深 SRE 工程师, 现在负责评估当前诊断进度并决策下一步。

# 决策原则
1. 信息充足时立刻收尾: 拿到关键证据后不要为了严谨继续无效排查。
2. 信息真不足时才继续: 如果关键证据缺失, 给出剩余步骤。
3. 不要重复: 已经完成的步骤不要再放进剩余计划里。
4. 避免死循环: 单次诊断步数尽量控制在 3 步以内。
5. 已执行 0 步时不要 is_finished=true; 已执行至少 1 步且能写出根因和建议时可以收尾。
6. 决定 is_finished=true 时, response 必须能填满问题概述、关键证据、根因分析、处置建议、结论。

# Skill reroute 决策
只有当前 Skill 方向明显不对时才设置 should_reroute=true。

应该 reroute:
- 当前 Skill 的关键证据明确不成立。
- 工具结果明显指向另一个故障域。
- 当前 Skill 的关键工具全部不可用。

不要 reroute:
- 某一步工具偶发失败。
- 只是想多查一些信息。
- 已超过最大步数。
- 当前方向只是证据不足, 还没证明错误。

# 最终报告格式
# 故障诊断报告
**生成时间**: <使用用户消息中提供的当前生成时间>

## 一、问题概述
- 现象: ...
- 影响范围: ...
- 持续时长: ...

## 二、根因分析
基于已收集的证据, 推断的根本原因是 ...

## 三、关键证据
1. ... (引用具体日志/指标/SOP)

## 四、处置建议
### 紧急止损
1. ...

### 长期优化
1. ...

## 五、结论
一句话结论。
"""

    _REPLANNER_USER_TEMPLATE = """# 用户原始问题
{input}

# 当前生成时间
{current_time}

# 当前选中的 Skill
{current_skill_line}

# 候选 Skill 菜单
{candidate_skills_text}

# 已尝试过的 Skill 黑名单
{tried_skills_text}

# Reroute 可用名额
当前 reroute_count = {reroute_count}, 上限 = {max_reroutes}
{reroute_quota_hint}

# 原始诊断计划
{plan_text}

# 已完成步骤及结果
{past_steps_text}

# 你的决策
请根据当前进度判断, 并以 JSON 格式输出。三种互斥情况选一:

情况 1: 信息已充足 → 出报告
- is_finished = true
- response = 完整诊断报告
- plan = [], should_reroute = false

情况 2: 信息不足, 但方向是对的 → 继续在当前 Skill 内 replan
- is_finished = false, should_reroute = false
- plan = ["剩余步骤 1", "剩余步骤 2"]
- response = ""

情况 3: 证据表明当前 Skill 方向错了 → reroute
- is_finished = false
- should_reroute = true
- new_skill = 候选 Skill 菜单里的名字
- reroute_reason = 引用具体证据的一句话
- plan = [], response = ""
"""

    _REPORT_SYSTEM_PROMPT = """你是一名资深 SRE 工程师, 基于已收集的证据写一份运维诊断报告。

# 硬性要求
1. 必须产出完整 5 段: 问题概述、关键证据、根因分析、处置建议、结论。
2. 证据段要引用关键指标/日志/SOP, 不要凭空编。
3. 处置建议按"紧急止损 / 长期优化"两小节。
4. 中文输出, 语气专业但不啰嗦。
5. 不要写"我将"这类过程性语言, 直接给结论。
"""

    _REPORT_USER_TEMPLATE = """# 用户原始问题
{user_input}

# 诊断流程中收集的证据
{past_steps_text}

# Replanner 初版结论
{draft}

# 报告生成时间
{current_time}

请严格按 5 段结构, 用 Markdown 输出最终报告。
"""

    _RAG_SYSTEM_PROMPT = """你是一名资深 SRE 工程师助手, 负责基于内部运维知识库回答工程师的问题。

# 回答要求
1. 优先使用提供的参考资料, 不要编造。
2. 使用资料时用 [来源 N] 标注引用; 使用联网资料时用 [联网 N] 标注引用。
3. 资料不足时诚实说明, 再基于通用经验给建议。
4. 复杂问题用 Markdown 分段。
5. 始终中文。
6. 如果用户要求执行高风险操作, 只给只读排查建议。
"""

    _RAG_TOOL_APPENDIX = """

# 工具调用
你可以调用只读工具实时查询系统状态。

# 何时调工具
- 用户问"现在怎么样"、"还在不在"、"好了没"、"是否解决"时, 必须先调工具。
- 用户追问最近一次诊断报告的当前状态时, 必须先调工具确认。
- 用户问原理/SOP/概念时, 不要乱调工具。
- 一次回答最多调 2-3 个工具, 工具结果尽量并行获取。

# 调工具后的回答规范
- 必须写出工具返回的具体数字/状态。
- 末尾用 Markdown 表格汇总关键指标。
- 如果工具失败, 说明哪个工具失败, 再基于知识库回答。
"""

    _RAG_USER_TEMPLATE = """# 会话摘要
{summary}

# 最近诊断报告
{diagnosis_context}

# 参考资料
{context}

# 联网补充资料
{web_context}

# 用户问题
{question}

请基于以上资料回答, 必要时标注 [来源 N]。若用户问"刚才/之前/这个"等指代, 优先参考最近诊断报告。
"""

    _RAG_REWRITE_TEMPLATE = """你是 RAG 检索查询改写器。
请根据会话摘要、最近对话和当前问题, 把当前问题改写成一个独立、完整、适合知识库检索的问题。

要求:
1. 如果当前问题已经完整, 直接原样返回。
2. 如果出现"这个/那个/刚才/上面说的", 要补全指代。
3. 不要回答问题, 只输出改写后的查询。
4. 保留关键英文 token、错误码、参数名。

# 会话摘要
{summary}

# 最近对话
{history}

# 当前问题
{question}

# 改写后的检索问题"""

    _RAG_COMPACT_TEMPLATE = """请总结这段 OnCall SOP 问答历史, 保留后续追问需要的信息。

必须包含:
1. 用户正在关注的系统/组件
2. 已讨论过的告警、参数、错误码
3. 已给过的关键处置建议
4. 用户明确表达的约束或偏好
5. 仍未解决/可能继续追问的问题

要求:
- 简洁
- 不要复制大段 SOP 原文
- 保留关键英文 token
- 不超过 {max_chars} 个中文字符

# 既有摘要
{old_summary}

# 本次需要合并进摘要的较早对话
{old_messages}

# 新摘要"""

    def router_model(self) -> str:
        return settings.dashscope_router_model

    def build_skill_router_messages(
        self,
        *,
        menu: str,
        user_input: str,
        generic: str,
        lessons: str = "",
    ) -> list[dict[str, str]]:
        lessons_section = (
            self._SKILL_ROUTER_LESSONS_TEMPLATE.format(lessons=lessons) if lessons else ""
        )
        return [
            {"role": "system", "content": self._SKILL_ROUTER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": self._SKILL_ROUTER_USER_TEMPLATE.format(
                    menu=menu,
                    input=user_input,
                    generic=generic,
                    lessons_section=lessons_section,
                ),
            },
        ]

    def planner_model(self) -> str:
        return settings.agent_planner_model or settings.dashscope_router_model

    def executor_model(self) -> str:
        return settings.agent_executor_model or settings.dashscope_chat_model

    def replanner_model(self) -> str:
        return settings.agent_planner_model or settings.dashscope_router_model

    def report_model(self) -> str:
        return settings.agent_report_model or settings.dashscope_chat_model

    def report_decision_model(self) -> str:
        return settings.agent_planner_model or settings.dashscope_router_model

    def rag_rewrite_model(self) -> str:
        return settings.dashscope_router_model

    def rag_compact_model(self) -> str:
        return settings.dashscope_chat_model

    def rag_chat_model(self) -> str:
        return settings.dashscope_chat_model

    def default_permission_mode(self) -> str:
        return settings.permission_mode

    def agent_max_concurrency(self) -> int:
        return settings.agent_max_concurrency

    def max_total_tokens(self) -> int:
        return max(0, settings.harness_max_total_tokens)

    def max_total_ms(self) -> int:
        return max(0, settings.harness_max_total_ms)

    def budget_warn_ratio(self) -> float:
        return min(1.0, max(0.0, settings.harness_budget_warn_ratio))

    def max_agent_steps(self) -> int:
        return settings.agent_max_steps

    def graph_recursion_limit(self) -> int:
        return self.max_agent_steps() * 3 + 5

    def max_reroutes(self) -> int:
        return settings.agent_max_reroutes

    def min_reroute_past_steps(self) -> int:
        return settings.agent_reroute_min_past_steps

    def replanner_past_step_chars(self) -> int:
        return max(200, settings.agent_replanner_past_step_chars)

    def executor_parallel_enabled(self) -> bool:
        return settings.executor_parallel_enabled

    def executor_policy(self) -> ToolRunnerPolicy:
        return ToolRunnerPolicy(
            max_iters=settings.executor_max_iters,
            max_parallel=settings.executor_max_parallel,
        )

    def rag_tool_policy(self) -> ToolRunnerPolicy:
        return ToolRunnerPolicy(
            max_iters=settings.rag_chat_max_tool_rounds,
            max_parallel=4,
        )

    def evaluate_budget(self, stats: HarnessUsageStats) -> HarnessBudgetStatus:
        warnings: list[str] = []
        exceeded = False
        token_limit = self.max_total_tokens()
        time_limit = self.max_total_ms()
        warn_ratio = self.budget_warn_ratio()

        if token_limit > 0 and stats.total_tokens > 0:
            token_ratio = stats.total_tokens / token_limit
            if stats.total_tokens >= token_limit:
                exceeded = True
                warnings.append("total_tokens_exceeded")
            elif token_ratio >= warn_ratio:
                warnings.append("total_tokens_near_limit")
        else:
            token_ratio = 0.0

        if time_limit > 0 and stats.total_ms > 0:
            time_ratio = stats.total_ms / time_limit
            if stats.total_ms >= time_limit:
                exceeded = True
                warnings.append("total_ms_exceeded")
            elif time_ratio >= warn_ratio:
                warnings.append("total_ms_near_limit")
        else:
            time_ratio = 0.0

        return HarnessBudgetStatus(
            exceeded=exceeded,
            warnings=warnings,
            data={
                "total_tokens": stats.total_tokens,
                "max_total_tokens": token_limit,
                "token_ratio": round(token_ratio, 4),
                "total_ms": stats.total_ms,
                "max_total_ms": time_limit,
                "time_ratio": round(time_ratio, 4),
                "warn_ratio": warn_ratio,
                "run_kind": stats.run_kind,
            },
        )

    def build_usage_stats_event(self, stats: HarnessUsageStats) -> dict[str, Any]:
        detail_parts = []
        if stats.input_tokens or stats.output_tokens or stats.total_tokens:
            detail_parts.append(
                f"输入 {stats.input_tokens} · 输出 {stats.output_tokens} · 合计 {stats.total_tokens} tokens"
            )
        if stats.llm_ms:
            detail_parts.append(f"生成 {stats.llm_ms}ms")
        detail_parts.append(f"总耗时 {stats.total_ms}ms")
        if stats.tool_calls:
            detail_parts.append(f"工具 {stats.tool_calls} 次")
        return {
            "type": "progress",
            "stage": "stats",
            "label": "本轮统计",
            "detail": " · ".join(detail_parts),
            "elapsed_ms": stats.llm_ms,
            "data": {
                "input_tokens": stats.input_tokens,
                "output_tokens": stats.output_tokens,
                "total_tokens": stats.total_tokens,
                "llm_ms": stats.llm_ms,
                "total_ms": stats.total_ms,
                "tool_calls": stats.tool_calls,
                "tool_ms": stats.tool_ms,
                "model": stats.model,
                "answer_chars": stats.answer_chars,
                "run_kind": stats.run_kind,
            },
        }

    def build_budget_event(self, status: HarnessBudgetStatus) -> dict[str, Any] | None:
        if not status.exceeded and not status.warnings:
            return None
        stage = "budget_exceeded" if status.exceeded else "budget_warning"
        label = "预算已超过" if status.exceeded else "预算接近上限"
        return {
            "type": "progress",
            "stage": stage,
            "label": label,
            "detail": ", ".join(status.warnings),
            "elapsed_ms": status.data.get("total_ms", 0),
            "data": status.data | {
                "exceeded": status.exceeded,
                "warnings": status.warnings,
            },
        }

    def build_planner_messages(
        self,
        *,
        user_input: str,
        skill_display_name: str,
        skill_playbook: str,
    ) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": self._PLANNER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": self._PLANNER_USER_TEMPLATE.format(
                    input=user_input,
                    skill_display_name=skill_display_name,
                    skill_playbook=skill_playbook,
                ),
            },
        ]

    def planner_fallback_plan(self, reason: str) -> list[str]:
        if reason == "empty_plan":
            return ["汇总现有信息, 给出诊断结论"]
        return ["查询知识库, 寻找类似问题的处理经验", "汇总现有信息, 给出诊断结论"]

    def executor_system_prompt(self) -> str:
        return self._EXECUTOR_SYSTEM_PROMPT

    def build_executor_task_prompt(
        self,
        *,
        plan: list[str],
        step_index: int,
        total_steps: int,
        current_step: str,
    ) -> str:
        plan_text = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(plan))
        return self._EXECUTOR_TASK_TEMPLATE.format(
            plan_text=plan_text,
            step_index=step_index,
            total_steps=total_steps,
            current_step=current_step,
        )

    def build_replanner_messages(
        self,
        *,
        user_input: str,
        current_time: str,
        current_skill_line: str,
        candidate_skills_text: str,
        tried_skills_text: str,
        reroute_count: int,
        reroute_quota_hint: str,
        plan_text: str,
        past_steps_text: str,
    ) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": self._REPLANNER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": self._REPLANNER_USER_TEMPLATE.format(
                    input=user_input,
                    current_time=current_time,
                    current_skill_line=current_skill_line,
                    candidate_skills_text=candidate_skills_text,
                    tried_skills_text=tried_skills_text,
                    reroute_count=reroute_count,
                    max_reroutes=self.max_reroutes(),
                    reroute_quota_hint=reroute_quota_hint,
                    plan_text=plan_text,
                    past_steps_text=past_steps_text,
                ),
            },
        ]

    def build_reroute_quota_hint(self, *, reroute_count: int, past_steps_count: int) -> str:
        quota_remaining = max(0, self.max_reroutes() - reroute_count)
        min_steps = self.min_reroute_past_steps()
        if quota_remaining == 0:
            return "⚠ reroute 名额已用完, 不允许再切 Skill, 请继续或收尾。"
        if past_steps_count < min_steps:
            return f"⚠ 证据不足 (past_steps={past_steps_count} < {min_steps}), 还不允许 reroute。"
        return f"可以 reroute (剩余 {quota_remaining} 次), 但仅限当前 Skill 方向明确不成立时。"

    def format_past_steps(self, past_steps: list[tuple[str, str]]) -> str:
        if not past_steps:
            return "(暂无已完成的步骤)"
        limit = self.replanner_past_step_chars()
        lines = []
        for i, (step, result) in enumerate(past_steps, 1):
            body = result if len(result) <= limit else result[:limit] + f"\n[... 已截断, 原长 {len(result)} 字符]"
            lines.append(f"## 步骤 {i}: {step}\n{body}")
        return "\n\n".join(lines)

    def build_report_messages(
        self,
        *,
        user_input: str,
        past_steps: list[tuple[str, str]],
        current_time: str,
        draft: str,
    ) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": self._REPORT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": self._REPORT_USER_TEMPLATE.format(
                    user_input=user_input,
                    past_steps_text=self.format_past_steps(past_steps),
                    draft=draft or "(Replanner 未提供草稿)",
                    current_time=current_time,
                ),
            },
        ]

    def rag_system_prompt(self, *, tools_enabled: bool) -> str:
        return self._RAG_SYSTEM_PROMPT + (self._RAG_TOOL_APPENDIX if tools_enabled else "")

    def build_rag_user_prompt(
        self,
        *,
        summary: str,
        diagnosis_context: str,
        context: str,
        web_context: str,
        question: str,
    ) -> str:
        return self._RAG_USER_TEMPLATE.format(
            summary=summary,
            diagnosis_context=diagnosis_context,
            context=context,
            web_context=web_context,
            question=question,
        )

    def build_rag_rewrite_prompt(
        self,
        *,
        summary: str,
        history: str,
        question: str,
    ) -> str:
        return self._RAG_REWRITE_TEMPLATE.format(
            summary=summary,
            history=history,
            question=question,
        )

    def build_rag_compact_prompt(
        self,
        *,
        max_chars: int,
        old_summary: str,
        old_messages: str,
    ) -> str:
        return self._RAG_COMPACT_TEMPLATE.format(
            max_chars=max_chars,
            old_summary=old_summary,
            old_messages=old_messages,
        )

    def evaluate_replanner_pre_llm(self, state: Mapping[str, Any]) -> HarnessDecision:
        plan = list(state.get("plan") or [])
        past_steps = list(state.get("past_steps") or [])
        iteration = int(state.get("iteration") or 0)

        if iteration >= self.max_agent_steps():
            return HarnessDecision(
                action="force_report",
                reason="max_steps_reached",
                data={"iteration": iteration, "max_steps": self.max_agent_steps()},
            )

        if self._has_repeated_steps(past_steps):
            return HarnessDecision(
                action="force_report",
                reason="repeated_steps_detected",
                data={"repeat_window": 3},
            )

        plan_remaining = max(0, len(plan) - 1)
        if (
            settings.agent_replanner_fast_path_threshold > 0
            and plan_remaining >= settings.agent_replanner_fast_path_threshold
            and not self._last_step_failed(past_steps)
            and iteration < self.max_agent_steps() - 1
        ):
            next_plan = list(plan[1:])
            return HarnessDecision(
                action="continue_fast_path",
                reason="fast_path",
                data={"next_plan": next_plan, "remaining": len(next_plan)},
            )

        return HarnessDecision(action="allow_llm", reason="needs_replanner_llm")

    def classify_error(self, exc: BaseException) -> ErrorKind:
        name = type(exc).__name__.lower()
        text = str(exc).lower()
        if "timeout" in name or "timeout" in text or "temporar" in text or "connection reset" in text:
            return "transient"
        if "tool" in text and ("argument" in text or "schema" in text or "validation" in text):
            return "llm_recoverable"
        if "api key" in text or "unauthorized" in text or "401" in text or "permission" in text:
            return "user_fixable"
        if "mcp" in text or "milvus" in text or "connection refused" in text:
            return "tool_unavailable"
        if name in {"typeerror", "attributeerror", "importerror", "modulenotfounderror", "nameerror", "keyerror"}:
            return "code_bug"
        return "unexpected"

    def rag_fallback(self, *, stage: str, exc: BaseException) -> dict[str, Any]:
        kind = self.classify_error(exc)
        detail = f"{type(exc).__name__}: {exc}"
        return {
            "context": "(知识库检索暂不可用，已降级为无知识库上下文回答。请基于已有会话、实时工具或通用运维知识回答，并明确说明知识库不可用。)",
            "sources": [],
            "hits_meta": [],
            "event_data": {
                "degraded": True,
                "stage": stage,
                "error_kind": kind,
                "error_type": type(exc).__name__,
                "error": detail[:500],
                "fallback": "no_rag_context",
            },
        }

    def web_fallback(self, *, stage: str, exc: BaseException) -> dict[str, Any]:
        kind = self.classify_error(exc)
        detail = f"{type(exc).__name__}: {exc}"
        return {
            "context": "(联网补充暂不可用，已跳过联网上下文。)",
            "sources": [],
            "hits": [],
            "skip_reason": f"{type(exc).__name__}: 联网补充失败",
            "event_data": {
                "degraded": True,
                "stage": stage,
                "error_kind": kind,
                "error_type": type(exc).__name__,
                "error": detail[:500],
                "fallback": "skip_web_context",
            },
        }

    def _last_step_failed(self, past_steps: list[Any]) -> bool:
        if not past_steps:
            return False
        try:
            result = past_steps[-1][1]
        except Exception:
            return False
        head = str(result or "")[:80]
        return head.startswith("[执行失败") or head.startswith("[超过最大步数")

    def _has_repeated_steps(self, past_steps: list[Any]) -> bool:
        if len(past_steps) < 3:
            return False
        fingerprints = []
        for item in past_steps[-3:]:
            try:
                step = item[0]
            except Exception:
                return False
            fingerprint = self._fingerprint_step(str(step))
            if not fingerprint:
                return False
            fingerprints.append(fingerprint)
        return len(set(fingerprints)) == 1

    def _fingerprint_step(self, text: str) -> str:
        return "".join(ch.lower() for ch in text if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")[:100]


_agent_harness = AgentHarness()


def get_agent_harness() -> AgentHarness:
    return _agent_harness
