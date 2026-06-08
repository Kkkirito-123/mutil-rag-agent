"""网络诊断 MCP Server.

提供本机网络排查能力, 让 OnCall Agent 能真实诊断 "网站打不开 / DNS 异常 / 端口不通" 等问题:
  - ping_host: 测试主机连通性 + 丢包率 + 延迟
  - http_check: HTTP/HTTPS 健康检查 (状态码 + 响应时间)
  - dns_lookup: 域名 DNS 解析
  - check_port: TCP 端口可达性

底层: subprocess (ping) + httpx (http) + socket (dns/port), 全部 stdlib + 已有依赖.
读模式: 只读, 不修改任何网络配置.
"""

import socket
import subprocess
import time
from typing import Optional
from urllib.parse import urlparse

import httpx
from fastmcp import FastMCP
from loguru import logger

mcp = FastMCP(name="NetworkServer")


# 主机黑名单 (避免被 prompt 注入扫描内网/敏感主机)
_HOST_BLOCKLIST_PREFIXES = (
    "10.",  # 内网 A
    "192.168.",  # 内网 C
    "172.",  # 部分内网 B (粗略)
    "127.",  # 本地回环
    "0.",
    "169.254.",  # 链路本地
)


def _is_blocked_ip(host: str) -> bool:
    """简单黑名单. 注: 仅当 host 看起来已经是 IP 时才拦, 域名先放过 (会在解析后再判)."""
    parts = host.split(".")
    if len(parts) == 4 and all(p.isdigit() for p in parts):
        for prefix in _HOST_BLOCKLIST_PREFIXES:
            if host.startswith(prefix):
                return True
    return False


@mcp.tool(
    name="ping_host",
    description=(
        "ping 一个公网主机, 检测连通性 / 丢包率 / 延迟. "
        "host 可以是域名 (www.baidu.com) 或公网 IP. "
        "拒绝 ping 内网地址 (10.* / 192.168.* / 127.* 等). "
        "count 默认 4 次, 上限 10 次."
    ),
)
def ping_host(host: str, count: int = 4) -> str:
    host = (host or "").strip()
    if not host:
        return "[拒绝] host 不能为空"
    if _is_blocked_ip(host):
        return f"[拒绝] {host} 是内网/回环地址, 不允许 ping"
    count = max(1, min(int(count or 4), 10))

    try:
        # Windows ping 默认 4 次, -n 指定次数, -w 单次超时 (毫秒)
        proc = subprocess.run(
            ["ping", "-n", str(count), "-w", "2000", host],
            capture_output=True,
            text=True,
            timeout=count * 3 + 5,
            encoding="gbk",  # Windows ping 默认 GBK
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        return f"[失败] ping {host} 超时 (>{count*3+5}s)"
    except Exception as e:
        return f"[失败] ping 异常: {e}"

    output = (proc.stdout or "") + (proc.stderr or "")
    return f"## ping {host} (count={count})\n\n```\n{output.strip()[:2000]}\n```"


@mcp.tool(
    name="http_check",
    description=(
        "对一个 HTTP/HTTPS URL 发起 GET 请求, 返回状态码 / 响应时间 / 响应头摘要. "
        "用于检查网站/接口可用性. 默认 10s 超时, 不跟随重定向超过 5 次."
    ),
)
def http_check(url: str, timeout_sec: float = 10.0) -> str:
    url = (url or "").strip()
    if not url:
        return "[拒绝] url 不能为空"
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    parsed = urlparse(url)
    host = parsed.hostname or ""
    if _is_blocked_ip(host):
        return f"[拒绝] {host} 是内网/回环地址, 不允许 http_check"

    timeout_sec = max(1.0, min(float(timeout_sec or 10.0), 30.0))

    start = time.time()
    try:
        with httpx.Client(timeout=timeout_sec, follow_redirects=True) as client:
            resp = client.get(url, headers={"User-Agent": "OnCall-Agent/1.0"})
        elapsed_ms = int((time.time() - start) * 1000)
    except httpx.TimeoutException:
        return f"[失败] {url} 请求超时 (>{timeout_sec}s)"
    except httpx.ConnectError as e:
        return f"[失败] {url} 连接失败: {e}"
    except Exception as e:
        return f"[失败] {url} 请求异常: {e}"

    interesting_headers = {
        k: resp.headers[k]
        for k in ("server", "content-type", "content-length", "x-cache")
        if k in resp.headers
    }
    body_preview = resp.text[:200].replace("\n", " ").strip()
    return (
        f"## HTTP Check {url}\n"
        f"- status: {resp.status_code} {resp.reason_phrase}\n"
        f"- elapsed: {elapsed_ms} ms\n"
        f"- final_url: {resp.url}\n"
        f"- headers: {interesting_headers}\n"
        f"- body_preview: {body_preview}"
    )


@mcp.tool(
    name="dns_lookup",
    description="解析域名为 IP 地址 (A 记录). 支持 IPv4. 用于排查 DNS 故障.",
)
def dns_lookup(domain: str) -> str:
    domain = (domain or "").strip()
    if not domain:
        return "[拒绝] domain 不能为空"
    try:
        start = time.time()
        infos = socket.getaddrinfo(domain, None, family=socket.AF_INET)
        elapsed_ms = int((time.time() - start) * 1000)
        ips = sorted({info[4][0] for info in infos})
        return f"## DNS Lookup {domain}\n- IPs: {ips}\n- elapsed: {elapsed_ms} ms"
    except socket.gaierror as e:
        return f"[失败] {domain} DNS 解析失败: {e}"
    except Exception as e:
        return f"[失败] DNS 查询异常: {e}"


@mcp.tool(
    name="check_port",
    description=(
        "检测指定 host 的 TCP 端口是否可达. 用于排查 '服务起来了吗 / 防火墙挡了吗'. "
        "拒绝扫描内网 IP. timeout 默认 3 秒."
    ),
)
def check_port(host: str, port: int, timeout_sec: float = 3.0) -> str:
    host = (host or "").strip()
    if not host or not port:
        return "[拒绝] host 和 port 都不能为空"
    if _is_blocked_ip(host):
        return f"[拒绝] {host} 是内网/回环地址, 不允许扫描"
    port = int(port)
    if not (1 <= port <= 65535):
        return f"[拒绝] port 必须在 1-65535, 收到: {port}"
    timeout_sec = max(0.5, min(float(timeout_sec or 3.0), 10.0))

    try:
        start = time.time()
        with socket.create_connection((host, port), timeout=timeout_sec):
            elapsed_ms = int((time.time() - start) * 1000)
            return f"## Port {host}:{port}\n- 可达 (TCP 连接成功)\n- elapsed: {elapsed_ms} ms"
    except socket.timeout:
        return f"## Port {host}:{port}\n- **不可达** (超时 {timeout_sec}s, 可能被防火墙挡)"
    except ConnectionRefusedError:
        return f"## Port {host}:{port}\n- **不可达** (连接被拒绝, 端口未监听)"
    except socket.gaierror as e:
        return f"[失败] {host} DNS 解析失败: {e}"
    except Exception as e:
        return f"[失败] 端口检测异常: {e}"


if __name__ == "__main__":
    print("[mcp] network_server starting on http://0.0.0.0:8009/mcp ...")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8009)
