"""§5 cc-haha 借鉴: 二级 Agent (Subagent) 注册中心.

Split the main OnCall executor into three focused helpers:

  | Subagent           | 职责                          | 工具池                                    |
  |--------------------|-------------------------------|-------------------------------------------|
  | evidence_collector | 只读证据收集 (指标/日志/进程)  | get_local_*, query_*, list_top_processes |
  | kb_researcher      | 本地 KB + 联网兜底搜索         | search_knowledge_base, web_search         |
  | report_writer      | 整理已有证据为 Markdown 报告    | (无工具, 纯 LLM)                          |

The main executor sees three `delegate_to_<agent_type>` tools, while each helper
keeps a focused prompt and a small tool set.

参考:
  cc-haha src/tools/AgentTool/built-in/*  (planAgent / generalPurposeAgent 等 6 种内置)
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class SubagentDefinition(BaseModel):
    """单个二级 Agent 的定义."""

    agent_type: str = Field(..., description="Subagent 唯一标识, 用于 delegate_to_<type>")
    display_name: str = Field(..., description="人类可读名称, 日志/前端展示")
    description: str = Field(
        ...,
        description="给主 Executor LLM 看的工具描述, 决定何时委托. **写清楚什么场景适合, 什么场景不要用**.",
    )
    system_prompt: str = Field(..., description="Subagent 自己的 system prompt")
    allowed_tools: List[str] = Field(
        default_factory=list,
        description="Subagent 能用的工具白名单 (subset of get_all_tools 中真实存在的工具名)",
    )
    max_iters: int = Field(default=3, description="Subagent 内部 LLM <-> tool 往返上限")
    max_result_chars: int = Field(
        default=8000,
        description="Subagent 返回给主 Executor 的字符上限 (超长截断)",
    )


# ============================================================
# 内置 subagent 定义
# ============================================================
SUBAGENTS: dict[str, SubagentDefinition] = {
    "evidence_collector": SubagentDefinition(
        agent_type="evidence_collector",
        display_name="证据收集助手",
        description=(
            "只读证据收集. 适合委托给它的任务: 拉某主机近 1 小时 CPU/内存指标; "
            "查某服务最近 30 分钟错误日志; 查 Windows 事件日志; 列 Top 进程; "
            "Docker 容器 ps/stats/logs/inspect; 网络 ping/dns/http/port. "
            "输入参数: task (要做什么的自然语言描述). "
            "**禁止用于检索知识库 / 发通知 / 写最终报告**."
        ),
        system_prompt=(
            "你是一个只读证据收集 Agent.\n"
            "你的目标: 用工具拉真实数据, 用 3-5 句话总结关键指标 / 异常日志 / 进程占用.\n"
            "纪律:\n"
            "  - 不做根因推理, 不给处置建议, 只汇报事实\n"
            "  - 同一类信息只查一次, 避免重复调用\n"
            "  - 拉到的数据如果超过 1000 字, 只挑最关键的 5-10 条原文 + 一段总结"
        ),
        allowed_tools=[
            # 本机系统 (psutil)
            "get_local_system_overview",
            "get_local_cpu_memory",
            "get_local_disk_usage",
            "list_top_processes",
            # Windows 事件日志
            "query_windows_event",
            # 网络诊断
            "ping_host",
            "http_check",
            "dns_lookup",
            "check_port",
            # Docker (只读)
            "docker_ps",
            "docker_stats",
            "docker_logs",
            "docker_inspect",
            # 通用
            "get_current_time",
        ],
        max_iters=3,
        max_result_chars=8000,
    ),
    "kb_researcher": SubagentDefinition(
        agent_type="kb_researcher",
        display_name="知识检索助手",
        description=(
            "本地知识库 + 联网兜底搜索. 适合委托: 查 SOP / 历史故障经验 / 陌生概念解释. "
            "输入参数: task (要查什么). "
            "**优先本地知识库, 不够才允许联网, web_search 最多 2 次**."
        ),
        system_prompt=(
            "你是一个知识检索 Agent.\n"
            "策略:\n"
            "  1. 先调 search_knowledge_base, 命中就用本地结果\n"
            "  2. 本地不够 / 主题陌生才用 web_search, 最多 2 次, 否则成本失控\n"
            "  3. 返回 Markdown 列表, 每条注明来源 (kb / web)\n"
            "  4. **只整理引用, 不要自己凭印象续写经验**"
        ),
        allowed_tools=["search_knowledge_base", "web_search"],
        max_iters=3,
        max_result_chars=6000,
    ),
    "report_writer": SubagentDefinition(
        agent_type="report_writer",
        display_name="报告写作助手",
        description=(
            "纯 LLM, 无工具. 适合委托: 把已有的证据 + 排查步骤合成最终 Markdown 故障报告. "
            "输入参数: task (要写什么报告). 调用前请把所有证据原文塞进 task 里. "
            "**不要用它收集信息, 只用它整理已有材料**."
        ),
        system_prompt=(
            "你是一个 SRE 报告整理 Agent, 没有任何工具.\n"
            "根据用户在 task 里给出的所有证据, 生成一份 Markdown 故障诊断报告, 包含 5 段:\n"
            "  1. 问题概述\n"
            "  2. 根因分析\n"
            "  3. 关键证据 (引用原始数据)\n"
            "  4. 处置建议\n"
            "  5. 结论\n"
            "纪律: 不能瞎编, 没证据的判断必须标 '推测' 或 '待确认'."
        ),
        allowed_tools=[],
        max_iters=1,  # 没工具, 一轮 LLM 调用就够
        max_result_chars=12000,
    ),
}


def get_subagent(agent_type: str) -> Optional[SubagentDefinition]:
    """按 agent_type 取定义, 不存在返回 None."""
    return SUBAGENTS.get(agent_type)
