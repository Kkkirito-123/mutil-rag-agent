import platform
from typing import Any, Dict, List

import psutil
from fastmcp import FastMCP

mcp = FastMCP(name="LocalSystemServer")


@mcp.tool(
    name="get_local_system_overview",
    description="获取当前电脑的 CPU、内存、磁盘和系统基础信息。只读操作，用于本机故障诊断。",
)
def get_local_system_overview() -> str:
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disks = []
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
                "total_gb": round(usage.total / 1024**3, 2),
                "used_gb": round(usage.used / 1024**3, 2),
                "free_gb": round(usage.free / 1024**3, 2),
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
        f"- 内存使用率: {memory.percent}% ({round(memory.used / 1024**3, 2)}GB / {round(memory.total / 1024**3, 2)}GB)",
        f"- Swap 使用率: {swap.percent}% ({round(swap.used / 1024**3, 2)}GB / {round(swap.total / 1024**3, 2)}GB)",
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


@mcp.tool(
    name="get_local_cpu_memory",
    description="获取当前电脑 CPU 和内存使用情况。只读操作，用于判断本机是否存在 CPU 或内存压力。",
)
def get_local_cpu_memory() -> str:
    cpu_total = psutil.cpu_percent(interval=1)
    cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)
    memory = psutil.virtual_memory()
    lines = [
        "## 本机 CPU / 内存",
        "",
        f"- CPU 总使用率: {cpu_total}%",
        f"- 每核心 CPU: {cpu_per_core}",
        f"- 内存使用率: {memory.percent}%",
        f"- 内存已用: {round(memory.used / 1024**3, 2)}GB",
        f"- 内存可用: {round(memory.available / 1024**3, 2)}GB",
        f"- 内存总量: {round(memory.total / 1024**3, 2)}GB",
    ]
    return "\n".join(lines)


@mcp.tool(
    name="get_local_disk_usage",
    description="获取当前电脑磁盘分区使用情况。只读操作，用于排查本机磁盘空间不足。",
)
def get_local_disk_usage() -> str:
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
            f"| {part.device} | {part.mountpoint} | {part.fstype} | {round(usage.used / 1024**3, 2)}GB | {round(usage.free / 1024**3, 2)}GB | {round(usage.total / 1024**3, 2)}GB | {usage.percent}% |"
        )
    return "\n".join(lines)


@mcp.tool(
    name="list_top_processes",
    description="列出当前电脑资源占用最高的进程。只读操作，用于定位 CPU 或内存占用来源。",
)
def list_top_processes(sort_by: str = "memory", limit: int = 10) -> List[Dict[str, Any]]:
    sort_by = (sort_by or "memory").lower().strip()
    if sort_by not in {"memory", "cpu"}:
        sort_by = "memory"
    limit = max(1, min(int(limit or 10), 30))

    processes = []
    for proc in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent", "memory_info"]):
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
                    "rss_mb": round((mem_info.rss if mem_info else 0) / 1024**2, 2),
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    key = "cpu_percent" if sort_by == "cpu" else "memory_percent"
    return sorted(processes, key=lambda item: item[key], reverse=True)[:limit]


if __name__ == "__main__":
    print("[mcp] system_server starting on http://0.0.0.0:8005/mcp ...")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8005)
