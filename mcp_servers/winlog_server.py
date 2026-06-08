"""Windows 事件日志查询 MCP Server.

提供查询本机 Windows 事件日志 (Event Log) 的能力, 用于诊断:
  - 系统崩溃 / 蓝屏 (Critical / Error)
  - 应用崩溃 (Application 日志的 Error)
  - 启动失败 / 服务异常
  - 安全事件 (登录失败等)

底层: 通过 PowerShell `Get-WinEvent` 命令读取, 避免依赖 pywin32.
读模式: 只读, 不修改任何系统状态.
"""

import json
import subprocess
from typing import Optional

from fastmcp import FastMCP
from loguru import logger

mcp = FastMCP(name="WindowsEventLogServer")


# 允许查询的日志通道白名单 (避免 prompt injection 触发奇怪通道)
_ALLOWED_LOGS = {"System", "Application", "Security", "Setup"}
# 单次返回上限, 防止巨量结果占满上下文
_MAX_RESULTS = 30


def _run_powershell(script: str, timeout: int = 20) -> tuple[str, str, int]:
    """执行 PowerShell 命令, 返回 (stdout, stderr, returncode)."""
    try:
        proc = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return proc.stdout or "", proc.stderr or "", proc.returncode
    except subprocess.TimeoutExpired:
        return "", "PowerShell 命令超时", -1
    except FileNotFoundError:
        return "", "未找到 powershell.exe (非 Windows 环境?)", -1


@mcp.tool(
    name="query_windows_event",
    description=(
        "查询本机 Windows 事件日志. 用于诊断蓝屏/崩溃/服务异常等本机故障. "
        "log_name: System / Application / Security / Setup, 默认 System. "
        "level: Critical(1) / Error(2) / Warning(3), 默认 Error 及以上. "
        "last_minutes: 查询最近多少分钟内的事件, 默认 60. "
        "max_count: 最多返回多少条, 默认 20, 上限 30."
    ),
)
def query_windows_event(
    log_name: str = "System",
    level: str = "Error",
    last_minutes: int = 60,
    max_count: int = 20,
) -> str:
    log_name = (log_name or "System").strip()
    if log_name not in _ALLOWED_LOGS:
        return f"[拒绝] log_name 必须是 {sorted(_ALLOWED_LOGS)} 之一, 收到: {log_name}"

    level_map = {"Critical": 1, "Error": 2, "Warning": 3, "Information": 4, "Verbose": 5}
    lv = level_map.get(level.capitalize(), 2)

    last_minutes = max(1, min(int(last_minutes or 60), 60 * 24))  # 最多查 24h
    max_count = max(1, min(int(max_count or 20), _MAX_RESULTS))

    # 用 Get-WinEvent + FilterHashtable, 比 Get-EventLog 新且性能好
    script = (
        f"$ErrorActionPreference='SilentlyContinue';"
        f"Get-WinEvent -FilterHashtable @{{LogName='{log_name}'; Level=1,2,3; "
        f"StartTime=(Get-Date).AddMinutes(-{last_minutes})}} -MaxEvents {max_count} | "
        f"Where-Object {{ $_.Level -le {lv} }} | "
        f"Select-Object TimeCreated, Id, LevelDisplayName, ProviderName, "
        f"@{{Name='Message';Expression={{$_.Message.Substring(0,[Math]::Min(300,$_.Message.Length))}}}} | "
        f"ConvertTo-Json -Compress -Depth 3"
    )

    stdout, stderr, code = _run_powershell(script)
    if code != 0 and not stdout:
        return f"[失败] PowerShell 返回 code={code}, stderr={stderr.strip()[:200]}"

    text = stdout.strip()
    if not text:
        return f"[空] 最近 {last_minutes} 分钟 {log_name} 日志中没有 {level} 及以上级别的事件"

    # 尝试解析 JSON 格式化输出
    try:
        events = json.loads(text)
        if isinstance(events, dict):
            events = [events]
    except json.JSONDecodeError:
        # PowerShell 偶尔会输出非 JSON, 直接返回原文
        return f"## {log_name} 日志 (最近 {last_minutes}min, {level}+)\n\n{text[:2000]}"

    if not events:
        return f"[空] 最近 {last_minutes} 分钟 {log_name} 日志中没有匹配事件"

    lines = [f"## {log_name} 日志 (最近 {last_minutes}min, 共 {len(events)} 条 {level}+)"]
    for ev in events:
        time_str = (ev.get("TimeCreated") or "")[:19].replace("T", " ")
        lines.append(
            f"\n### [{time_str}] {ev.get('LevelDisplayName','?')} "
            f"event_id={ev.get('Id','?')} source={ev.get('ProviderName','?')}\n"
            f"{(ev.get('Message') or '').strip()}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    print("[mcp] winlog_server starting on http://0.0.0.0:8008/mcp ...")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8008)
