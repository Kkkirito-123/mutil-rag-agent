"""Docker 容器管理 MCP Server.

提供本机 Docker 容器的查询能力, 用于诊断 "Milvus / Redis / 数据库容器是不是挂了":
  - docker_ps: 列出所有容器及状态
  - docker_stats: 容器资源占用 (CPU/MEM)
  - docker_logs: 拉取容器最近日志
  - docker_inspect: 容器详细信息
  - docker_restart: 重启容器 (写操作, 默认禁用, 需明确开启)

底层: subprocess 调用 docker CLI, 无需 docker-py 依赖.
读模式: 默认只读. docker_restart 通过 DOCKER_ALLOW_RESTART=true 开启.
"""

import json
import os
import subprocess
from typing import List, Optional

from dotenv import load_dotenv
from fastmcp import FastMCP
from loguru import logger

load_dotenv()

mcp = FastMCP(name="DockerServer")

DOCKER_ALLOW_RESTART = os.getenv("DOCKER_ALLOW_RESTART", "false").lower() in (
    "true",
    "1",
    "yes",
)
_MAX_LOG_LINES = 200


def _run_docker(args: List[str], timeout: int = 15) -> tuple[str, str, int]:
    try:
        proc = subprocess.run(
            ["docker", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return proc.stdout or "", proc.stderr or "", proc.returncode
    except subprocess.TimeoutExpired:
        return "", f"docker 命令超时 (>{timeout}s)", -1
    except FileNotFoundError:
        return "", "未找到 docker 命令 (是否未安装 / 未启动 Docker Desktop?)", -1


@mcp.tool(
    name="docker_ps",
    description=(
        "列出本机所有 Docker 容器 (含已停止). 返回容器名 / 镜像 / 状态 / 端口映射. "
        "用于排查某个容器是否在运行."
    ),
)
def docker_ps() -> str:
    stdout, stderr, code = _run_docker(["ps", "-a", "--format", "{{json .}}"])
    if code != 0:
        return f"[失败] docker ps 失败: {stderr.strip()[:300]}"
    if not stdout.strip():
        return "[空] 本机没有任何 Docker 容器"

    lines = ["## 本机 Docker 容器列表", ""]
    lines.append("| 容器名 | 镜像 | 状态 | 端口 |")
    lines.append("|---|---|---|---|")
    for line in stdout.strip().splitlines():
        try:
            c = json.loads(line)
        except json.JSONDecodeError:
            continue
        name = c.get("Names", "")
        image = c.get("Image", "")[:40]
        status = c.get("Status", "")
        ports = c.get("Ports", "")[:60]
        lines.append(f"| {name} | {image} | {status} | {ports} |")
    return "\n".join(lines)


@mcp.tool(
    name="docker_stats",
    description=(
        "查看一个容器的实时资源占用 (CPU% / 内存使用 / 网络IO / 磁盘IO). "
        "name 为容器名 (从 docker_ps 拿到). 一次性快照, 不持续监控."
    ),
)
def docker_stats(name: str) -> str:
    name = (name or "").strip()
    if not name:
        return "[拒绝] name 不能为空"
    stdout, stderr, code = _run_docker(
        ["stats", "--no-stream", "--format", "{{json .}}", name]
    )
    if code != 0:
        return f"[失败] docker stats {name} 失败: {stderr.strip()[:300]}"
    if not stdout.strip():
        return f"[空] 容器 {name} 不存在或未运行"

    try:
        s = json.loads(stdout.strip().splitlines()[0])
    except json.JSONDecodeError:
        return f"## docker stats {name}\n\n```\n{stdout.strip()[:1000]}\n```"

    return (
        f"## 容器 {name} 资源占用\n"
        f"- CPU: {s.get('CPUPerc','?')}\n"
        f"- 内存: {s.get('MemUsage','?')} ({s.get('MemPerc','?')})\n"
        f"- 网络IO: {s.get('NetIO','?')}\n"
        f"- 磁盘IO: {s.get('BlockIO','?')}\n"
        f"- PIDs: {s.get('PIDs','?')}"
    )


@mcp.tool(
    name="docker_logs",
    description=(
        "拉取一个容器的最近日志, 用于排查容器内应用错误. "
        "name 为容器名. tail 为返回最近多少行 (默认 50, 上限 200). "
        "since_minutes 可选, 只看最近 N 分钟的日志."
    ),
)
def docker_logs(
    name: str, tail: int = 50, since_minutes: Optional[int] = None
) -> str:
    name = (name or "").strip()
    if not name:
        return "[拒绝] name 不能为空"
    tail = max(1, min(int(tail or 50), _MAX_LOG_LINES))

    args = ["logs", "--tail", str(tail)]
    if since_minutes:
        args.extend(["--since", f"{int(since_minutes)}m"])
    args.append(name)

    stdout, stderr, code = _run_docker(args, timeout=20)
    if code != 0:
        return f"[失败] docker logs {name} 失败: {stderr.strip()[:300]}"

    # docker logs stdout/stderr 都可能有日志, 合并
    combined = (stdout + "\n" + stderr).strip()
    if not combined:
        return f"[空] 容器 {name} 无日志"
    if len(combined) > 4000:
        combined = combined[-4000:]
        combined = "...(已截断, 仅显示最后 4000 字符)\n" + combined
    return f"## docker logs {name} (tail={tail})\n\n```\n{combined}\n```"


@mcp.tool(
    name="docker_inspect",
    description=(
        "查看容器的详细配置 (镜像 / 启动命令 / 挂载卷 / 网络模式 / 重启策略). "
        "用于排查 '为什么这个容器一直重启' 等深度问题."
    ),
)
def docker_inspect(name: str) -> str:
    name = (name or "").strip()
    if not name:
        return "[拒绝] name 不能为空"
    stdout, stderr, code = _run_docker(["inspect", name])
    if code != 0:
        return f"[失败] docker inspect {name} 失败: {stderr.strip()[:300]}"
    try:
        data = json.loads(stdout)
        if isinstance(data, list) and data:
            data = data[0]
    except json.JSONDecodeError:
        return f"## docker inspect {name}\n\n```\n{stdout[:2000]}\n```"

    state = data.get("State", {})
    config = data.get("Config", {})
    host_config = data.get("HostConfig", {})
    return (
        f"## 容器 {name} 详细信息\n"
        f"- 状态: {state.get('Status','?')} (running={state.get('Running')})\n"
        f"- 启动于: {state.get('StartedAt','?')}\n"
        f"- 重启次数: {data.get('RestartCount', 0)}\n"
        f"- 镜像: {config.get('Image','?')}\n"
        f"- 命令: {config.get('Cmd')}\n"
        f"- 重启策略: {host_config.get('RestartPolicy',{}).get('Name','?')}\n"
        f"- 退出码: {state.get('ExitCode','?')}\n"
        f"- 错误信息: {state.get('Error','') or '(无)'}"
    )


@mcp.tool(
    name="docker_restart",
    description=(
        "重启一个容器 (写操作). **默认禁用**, 需要在 .env 设置 DOCKER_ALLOW_RESTART=true 才能调用. "
        "用于挂掉的容器恢复. 调用前最好先 docker_logs 看下原因."
    ),
)
def docker_restart(name: str) -> str:
    if not DOCKER_ALLOW_RESTART:
        return (
            "[拒绝] docker_restart 是危险操作, 默认禁用. "
            "如确需开启, 在 .env 设置 DOCKER_ALLOW_RESTART=true 并重启 MCP server."
        )
    name = (name or "").strip()
    if not name:
        return "[拒绝] name 不能为空"
    logger.warning(f"[Docker] 即将重启容器 {name}")
    stdout, stderr, code = _run_docker(["restart", name], timeout=30)
    if code != 0:
        return f"[失败] docker restart {name} 失败: {stderr.strip()[:300]}"
    return f"[成功] 容器 {name} 已重启"


if __name__ == "__main__":
    print("[mcp] docker_server starting on http://0.0.0.0:8011/mcp ...")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8011)
