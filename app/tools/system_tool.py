"""本机系统诊断工具 (本地 @tool, 与 MCP system_server 同名等价实现).

为什么同时存在本地和 MCP 两套:
  - MCP 版本 (mcp_servers/system_server.py) 保留 "可独立进程运行 / 远程调用" 的能力
  - 本地版本保证 "MCP 起不来时 Agent 仍能诊断本机", 不再硬依赖 MCP 进程
  - 在 mcp_loader.get_all_tools() 里做去重, 本地优先, 避免 LangChain 同名工具冲突

工具名与 Skill 的 allowed_tools 严格一致, SKILL.md 不用改:
  - get_local_system_overview
  - get_local_cpu_memory
  - get_local_disk_usage
  - list_top_processes
"""

from __future__ import annotations

import platform
from typing import Any, Dict, List

import psutil
from langchain_core.tools import tool
from loguru import logger


@tool
def get_local_system_overview() -> str:
    """获取当前电脑的 CPU、内存、磁盘和系统基础信息.

    在用户询问"我的电脑 / 本机 / 这台机器"出现卡顿、发热、资源异常时调用.
    返回 Markdown 表格, 可以直接写进诊断报告里.

    Returns:
        本机系统总览 (Markdown)
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disks: list[dict] = []
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except OSError:
                continue
            disks.append(
                {
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "total_gb": round(usage.total / 1024 ** 3, 2),
                    "used_gb": round(usage.used / 1024 ** 3, 2),
                    "free_gb": round(usage.free / 1024 ** 3, 2),
                    "percent": usage.percent,
                }
            )

        lines = [
            "## 本机系统概览",
            "",
            f"- 系统: {platform.system()} {platform.release()} ({platform.version()})",
            f"- 机器: {platform.machine()}",
            f"- CPU 核心: 物理 {psutil.cpu_count(logical=False) or '未知'} / 逻辑 {psutil.cpu_count(logical=True) or '未知'}",
            f"- CPU 使用率: {cpu_percent}%",
            f"- 内存使用率: {memory.percent}% ({round(memory.used / 1024 ** 3, 2)}GB / {round(memory.total / 1024 ** 3, 2)}GB)",
            f"- Swap 使用率: {swap.percent}% ({round(swap.used / 1024 ** 3, 2)}GB / {round(swap.total / 1024 ** 3, 2)}GB)",
            "",
            "## 磁盘",
            "",
            "| 挂载点 | 文件系统 | 已用 | 可用 | 总量 | 使用率 |",
            "|---|---|---:|---:|---:|---:|",
        ]
        for disk in disks:
            lines.append(
                f"| {disk['mountpoint']} | {disk['fstype']} | {disk['used_gb']}GB | {disk['free_gb']}GB | {disk['total_gb']}GB | {disk['percent']}% |"
            )
        return "\n".join(lines)
    except Exception as e:
        logger.exception(f"[system_tool] get_local_system_overview 失败: {e}")
        return f"本机系统信息采集失败: {type(e).__name__}: {e}"


@tool
def get_local_cpu_memory() -> str:
    """获取当前电脑 CPU 和内存使用情况.

    用于判断本机是否真的存在 CPU 或内存压力 (而不是主观感受).

    Returns:
        CPU/内存指标 (Markdown)
    """
    try:
        cpu_total = psutil.cpu_percent(interval=1)
        cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)
        memory = psutil.virtual_memory()
        lines = [
            "## 本机 CPU / 内存",
            "",
            f"- CPU 总使用率: {cpu_total}%",
            f"- 每核心 CPU: {cpu_per_core}",
            f"- 内存使用率: {memory.percent}%",
            f"- 内存已用: {round(memory.used / 1024 ** 3, 2)}GB",
            f"- 内存可用: {round(memory.available / 1024 ** 3, 2)}GB",
            f"- 内存总量: {round(memory.total / 1024 ** 3, 2)}GB",
        ]
        return "\n".join(lines)
    except Exception as e:
        logger.exception(f"[system_tool] get_local_cpu_memory 失败: {e}")
        return f"本机 CPU/内存采集失败: {type(e).__name__}: {e}"


@tool
def get_local_disk_usage() -> str:
    """获取当前电脑磁盘分区使用情况.

    排查"磁盘满 / 无空间 / 写入失败"之类问题时调用.

    Returns:
        磁盘使用情况 (Markdown 表格)
    """
    try:
        lines = [
            "## 本机磁盘使用情况",
            "",
            "| 设备 | 挂载点 | 文件系统 | 已用 | 可用 | 总量 | 使用率 |",
            "|---|---|---|---:|---:|---:|---:|",
        ]
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except OSError:
                continue
            lines.append(
                f"| {part.device} | {part.mountpoint} | {part.fstype} | "
                f"{round(usage.used / 1024 ** 3, 2)}GB | "
                f"{round(usage.free / 1024 ** 3, 2)}GB | "
                f"{round(usage.total / 1024 ** 3, 2)}GB | "
                f"{usage.percent}% |"
            )
        return "\n".join(lines)
    except Exception as e:
        logger.exception(f"[system_tool] get_local_disk_usage 失败: {e}")
        return f"本机磁盘采集失败: {type(e).__name__}: {e}"


@tool
def list_top_processes(sort_by: str = "memory", limit: int = 10) -> List[Dict[str, Any]]:
    """列出当前电脑资源占用最高的进程.

    用于定位 "到底是哪个程序把 CPU/内存 拉高的", 例如 Chrome / WSL / 杀毒.

    Args:
        sort_by: 排序方式, "memory" (默认) 或 "cpu"
        limit:   返回前 N 个进程 (1-30, 默认 10)

    Returns:
        进程列表, 每项含 pid/name/username/cpu_percent/memory_percent/rss_mb
    """
    try:
        key_raw = (sort_by or "memory").lower().strip()
        if key_raw not in {"memory", "cpu"}:
            key_raw = "memory"
        limit = max(1, min(int(limit or 10), 30))

        processes: list[dict] = []
        for proc in psutil.process_iter(
            ["pid", "name", "username", "cpu_percent", "memory_percent", "memory_info"]
        ):
            try:
                info = proc.info
                mem_info = info.get("memory_info")
                processes.append(
                    {
                        "pid": info.get("pid"),
                        "name": info.get("name"),
                        "username": info.get("username"),
                        "cpu_percent": round(float(info.get("cpu_percent") or 0), 2),
                        "memory_percent": round(float(info.get("memory_percent") or 0), 2),
                        "rss_mb": round((mem_info.rss if mem_info else 0) / 1024 ** 2, 2),
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        key = "cpu_percent" if key_raw == "cpu" else "memory_percent"
        return sorted(processes, key=lambda item: item[key], reverse=True)[:limit]
    except Exception as e:
        logger.exception(f"[system_tool] list_top_processes 失败: {e}")
        return [{"error": f"{type(e).__name__}: {e}"}]
