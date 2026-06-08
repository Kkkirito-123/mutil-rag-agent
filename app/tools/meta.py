"""工具元数据注册中心 (Tool Metadata Registry).

集中声明每个工具的安全语义和性能语义, 给 Harness / 编排层 / 审计层共享:
  - read_only: 是否只读 (不修改任何外部状态)
  - concurrency_safe: 是否可与同类工具同时并发执行 (一般 read_only=True 才安全)
  - destructive: 是否破坏性 (重启 / 删除 / 不可逆)
  - side_effect: none / external / filesystem / network
  - risk_level: low / medium / high
  - max_result_chars: 工具输出截断阈值 (避免一坨 20KB 日志直接喂 LLM)
  - search_hint: 给未来的 ToolSearch 二级动态发现用 (cc-haha 同款)

设计原则 (fail-closed):
  - 未在 TOOL_META 登记的工具会拿到保守默认: 不可并发 + 非只读 + 视为有副作用
  - 新增工具时必须在 TOOL_META 里登记, 否则会被并行编排和未来 PermissionMode 默认拦截
  - register_tool_meta() 用于 MCP 等运行时动态加载的工具补登记

参考: cc-haha src/Tool.ts:362-470 中的 isConcurrencySafe / isReadOnly / isDestructive 设计
"""

from __future__ import annotations

from typing import Callable, Dict, Literal, Optional

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field


SideEffect = Literal["none", "external", "filesystem", "network"]
RiskLevel = Literal["low", "medium", "high"]


class ToolMeta(BaseModel):
    """单个工具的元数据声明.

    所有字段均有保守默认值 (fail-closed). 未声明的工具会被视作:
        read_only=False, concurrency_safe=False, destructive=False, side_effect=none

    这意味着未登记的工具:
      - 在 §3 的并行编排里只会串行执行 (安全)
      - 在 §1 的 ASK_DESTRUCTIVE 模式下会被默认 ASK (因为 read_only=False)
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=False)

    read_only: bool = Field(
        default=False,
        description="不修改任何外部状态 (只读查询).",
    )
    concurrency_safe: bool = Field(
        default=False,
        description="多实例同时并发调用不会相互干扰; 一般 read_only=True 才安全.",
    )
    destructive: bool = Field(
        default=False,
        description="不可逆操作 (重启 / 删除 / 扣款); 通常 ASK_DESTRUCTIVE 模式下需人工确认.",
    )
    side_effect: SideEffect = Field(
        default="none",
        description="副作用类别: none / external / filesystem / network.",
    )
    is_notification: bool = Field(
        default=False,
        description=(
            "是否为外发通知类工具. "
            "受 settings.guardrails_allow_notification_tools 单独控制. "
            "注意: side_effect=external 不等同于 is_notification, "
            "例如 mcp_execute_tool 也是 external 但不是通知."
        ),
    )
    risk_level: RiskLevel = Field(
        default="low",
        description="风险等级: low (只读查询) / medium (外发通知 / 联网) / high (写操作).",
    )
    max_result_chars: int = Field(
        default=16000,
        description="工具结果上限字符数, 超过后由编排层截断或落盘 (cc-haha 是 maxResultSizeChars).",
    )
    search_hint: Optional[str] = Field(
        default=None,
        description="供 ToolSearch 二级动态发现使用的关键字 (cc-haha 同款).",
    )

    # 输入参数感知 (例如 cc-haha Bash 工具按命令决定是否只读). 当前不强求实现, 占位.
    is_read_only_for_input: Optional[Callable[[dict], bool]] = Field(
        default=None,
        description="可选: 根据输入决定是否只读, 优先于 read_only 字段.",
    )

    def effective_read_only(self, tool_input: Optional[dict] = None) -> bool:
        """根据输入计算最终的只读判定; 异常时回退静态 read_only 字段."""
        if self.is_read_only_for_input is not None and tool_input is not None:
            try:
                return bool(self.is_read_only_for_input(tool_input))
            except Exception as exc:  # pragma: no cover - 防御式
                logger.debug(
                    f"[ToolMeta] is_read_only_for_input 抛错, 回退静态 read_only={self.read_only}: {exc}"
                )
        return self.read_only


# ============================================================
# 中央注册表
# ============================================================
# 顺序: 本地 → 系统 → 监控/日志 → 联网 → 网络诊断 → 通知/写操作 → Lazy MCP
# ============================================================
TOOL_META: Dict[str, ToolMeta] = {
    # ===== 本地工具 =====
    "search_knowledge_base": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        max_result_chars=8000,
        risk_level="low",
        search_hint="rag knowledge base sop 知识库 经验",
    ),
    "get_current_time": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        max_result_chars=200,
        risk_level="low",
        search_hint="time clock 时间",
    ),

    # ===== 本机系统 (system_server.py) =====
    "get_local_system_overview": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        max_result_chars=4000,
        risk_level="low",
        search_hint="local system overview cpu memory disk 本机 概览",
    ),
    "get_local_cpu_memory": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        max_result_chars=2000,
        risk_level="low",
        search_hint="local cpu memory 本机 cpu 内存",
    ),
    "get_local_disk_usage": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        max_result_chars=2000,
        risk_level="low",
        search_hint="local disk usage 本机 磁盘",
    ),
    "list_top_processes": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        max_result_chars=4000,
        risk_level="low",
        search_hint="top processes 进程",
    ),

    # ===== Prometheus (prom_tool.py) =====
    # 真指标后端: 4 个只读 PromQL 工具. 未配 PROMETHEUS_URL 时仍可注册, 工具内自降级.
    "prom_query": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        side_effect="network",
        max_result_chars=6000,
        risk_level="low",
        search_hint="prometheus promql instant 即时 指标 metric",
    ),
    "prom_query_range": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        side_effect="network",
        max_result_chars=8000,
        risk_level="low",
        search_hint="prometheus promql range 时间序列 趋势",
    ),
    "prom_active_alerts": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        side_effect="network",
        max_result_chars=6000,
        risk_level="low",
        search_hint="prometheus alerts firing 活跃告警",
    ),
    "prom_label_values": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        side_effect="network",
        max_result_chars=3000,
        risk_level="low",
        search_hint="prometheus label values 标签 取值 发现",
    ),

    # ===== Windows 事件日志 (winlog_server.py) =====
    "query_windows_event": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        max_result_chars=20000,
        risk_level="low",
        search_hint="windows event log 蓝屏 崩溃",
    ),

    # ===== 联网搜索 (websearch_server.py) =====
    "web_search": ToolMeta(
        read_only=True,
        # 注意: 不并发. 外部搜索/本地 daemon 都应避免被 LLM 批量打爆.
        concurrency_safe=False,
        side_effect="network",
        max_result_chars=12000,
        risk_level="medium",
        search_hint="web search internet google bing 联网 搜索",
    ),

    # ===== 网络诊断 (network_server.py) =====
    "ping_host": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        side_effect="network",
        max_result_chars=2500,
        risk_level="low",
        search_hint="ping connectivity 连通性 丢包",
    ),
    "http_check": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        side_effect="network",
        max_result_chars=4000,
        risk_level="low",
        search_hint="http check 状态码 url 健康",
    ),
    "dns_lookup": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        side_effect="network",
        max_result_chars=1500,
        risk_level="low",
        search_hint="dns lookup 域名 解析",
    ),
    "check_port": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        side_effect="network",
        max_result_chars=1000,
        risk_level="low",
        search_hint="port tcp 端口 防火墙",
    ),

    # ===== Docker (docker_server.py) =====
    # 只读 docker_ps / docker_stats / docker_logs / docker_inspect 都是 low.
    # docker_restart 是写操作, high.
    "docker_ps": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        max_result_chars=6000,
        risk_level="low",
        search_hint="docker ps containers 容器 列表",
    ),
    "docker_stats": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        max_result_chars=2000,
        risk_level="low",
        search_hint="docker stats 资源 占用",
    ),
    "docker_logs": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        max_result_chars=20000,
        risk_level="low",
        search_hint="docker logs 容器 日志",
    ),
    "docker_inspect": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        max_result_chars=8000,
        risk_level="low",
        search_hint="docker inspect 容器 配置",
    ),
    "docker_restart": ToolMeta(
        read_only=False,
        concurrency_safe=False,
        destructive=True,
        side_effect="filesystem",
        risk_level="high",
        max_result_chars=1000,
        search_hint="docker restart 重启 容器",
    ),

    # ===== 通知 / 外发 =====

    # ===== Lazy MCP 元工具 =====
    # mcp_search_tools 是只读的工具发现入口, 可并发.
    # mcp_execute_tool 是动态执行入口, 由它内部再做安全决策, 这里保守不并发.
    "mcp_search_tools": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        max_result_chars=4000,
        risk_level="low",
        search_hint="mcp search lazy tools 搜索 mcp",
    ),
    "mcp_execute_tool": ToolMeta(
        read_only=False,
        concurrency_safe=False,
        side_effect="external",
        risk_level="medium",
        max_result_chars=20000,
        search_hint="mcp execute call 调用 mcp",
    ),

    # ===== §5 二级 Agent (Subagent) delegate 工具 =====
    # 主 Executor 通过 delegate_to_<agent_type> 把脏活分给小弟,
    # 内部调 LLM + 工具循环, 主对话只看到一段精炼总结.
    # 多个 delegate_to_evidence_collector / kb_researcher 同时进可并行 (各自子上下文独立).
    "delegate_to_evidence_collector": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        risk_level="low",
        max_result_chars=8000,
        search_hint="evidence collect metrics logs processes 证据 指标 日志",
    ),
    "delegate_to_kb_researcher": ToolMeta(
        read_only=True,
        concurrency_safe=True,
        side_effect="network",  # 内部可能联网
        risk_level="medium",
        max_result_chars=6000,
        search_hint="knowledge research sop kb web 知识 搜索",
    ),
    "delegate_to_report_writer": ToolMeta(
        read_only=True,
        concurrency_safe=False,  # 一般一份报告就够, 不需要并发
        risk_level="low",
        max_result_chars=12000,
        search_hint="report writer rca markdown 报告 写作",
    ),
}


# ============================================================
# 公共 API
# ============================================================
_CONSERVATIVE_DEFAULT = ToolMeta()  # read_only=False, concurrency_safe=False, ...


def get_meta(tool_name: str) -> ToolMeta:
    """查询工具元数据.

    未登记的工具返回保守默认 (read_only=False / concurrency_safe=False),
    确保 fail-closed 安全语义.
    """
    return TOOL_META.get(tool_name, _CONSERVATIVE_DEFAULT)


def is_registered(tool_name: str) -> bool:
    """判断工具是否在中央注册表中显式登记 (排除保守默认兜底)."""
    return tool_name in TOOL_META


def register_tool_meta(tool_name: str, meta: ToolMeta, *, override: bool = False) -> None:
    """运行时补登记元数据 (例如 MCP 工具加载完成后).

    Args:
        tool_name: 工具名称
        meta: 元数据
        override: 已存在时是否覆盖, 默认 False (避免误改静态声明)
    """
    if not override and tool_name in TOOL_META:
        logger.debug(f"[ToolMeta] {tool_name} 已存在静态声明, 不覆盖 (传 override=True 强制)")
        return
    TOOL_META[tool_name] = meta
    logger.debug(f"[ToolMeta] 注册 {tool_name}: read_only={meta.read_only} risk={meta.risk_level}")


def warn_unregistered_tools(tool_names: list[str]) -> list[str]:
    """对一批工具名做登记完整性检查, 返回未登记的子集 (并打 warning).

    建议在 get_all_tools() 加载完毕后调用一次, 帮助开发者发现新增工具忘记登记的情况.
    """
    missing = [name for name in tool_names if name not in TOOL_META]
    if missing:
        logger.warning(
            f"[ToolMeta] 以下工具未在 TOOL_META 登记, 将按保守默认 (非只读 / 不可并发) 处理: "
            f"{sorted(missing)}. 请在 app/tools/meta.py 补登记, 否则会影响并行编排和 PermissionMode 决策."
        )
    return missing


def summarize_registry() -> dict:
    """生成注册表汇总 (用于 /api 健康检查或启动日志).

    Returns:
        dict: 各 risk_level / read_only / concurrency_safe 的工具数和示例.
    """
    by_risk: Dict[str, list[str]] = {"low": [], "medium": [], "high": []}
    read_only_count = 0
    concurrency_safe_count = 0
    for name, meta in TOOL_META.items():
        by_risk[meta.risk_level].append(name)
        if meta.read_only:
            read_only_count += 1
        if meta.concurrency_safe:
            concurrency_safe_count += 1
    return {
        "total_registered": len(TOOL_META),
        "read_only": read_only_count,
        "concurrency_safe": concurrency_safe_count,
        "by_risk": {k: sorted(v) for k, v in by_risk.items()},
    }
