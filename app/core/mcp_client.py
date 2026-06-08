"""MCP 客户端管理.

通过 langchain_mcp_adapters.MultiServerMCPClient 加载远程 MCP 工具.

设计要点:
  - graceful degradation: MCP 服务挂了不影响应用启动 (RAG 仍可用)
  - 配置兼容: settings.mcp_servers 用 'streamable-http' 风格命名,
    本模块自动转换为 v1 adapter 期望的 'streamable_http'
  - 工具缓存: 启动时逐个 server 调 get_tools(server_name=...), 单点失败不影响其它
  - 不持有连接: MCP adapter 是 stateless 的, 每次调用工具时才建立短连接

为什么不用 client.get_tools() 一把梭:
  langchain-mcp-adapters 0.2.x 的 get_tools() 内部是
  `asyncio.gather(*tasks)` (无 return_exceptions), 再叠加底层
  streamablehttp_client 的 anyio.TaskGroup, 任意一个 server 失败都会
  把整批拒绝, 错误外层只能看到 'ExceptionGroup ... (1 sub-exception)',
  既丢了好的工具, 又看不到根因. 这里改成逐 server 加载 + 单次重试,
  并把 ExceptionGroup 展开打印, 解决"启动时偶发全军覆没"的问题.

使用:
    # main.py lifespan
    await mcp_client_manager.connect()
    tools = mcp_client_manager.tools  # List[BaseTool]
"""

import asyncio
from typing import Any, Dict, List, Optional

from langchain_core.tools import BaseTool
from loguru import logger

from app.config import settings


def _format_exc(e: BaseException) -> str:
    """把 ExceptionGroup 展开成可读的一行串.

    Python 3.11+ 的 ExceptionGroup 默认 str() 只会显示
    'unhandled errors in a TaskGroup (N sub-exception)', 完全看不到
    内层异常. 这里递归取出所有叶子异常, 方便排错.
    """
    eg_cls = getattr(__builtins__, "BaseExceptionGroup", None) or BaseException
    # Python 3.11+ 内置 BaseExceptionGroup
    try:
        from builtins import BaseExceptionGroup as _BEG  # type: ignore
        eg_cls = _BEG
    except ImportError:
        eg_cls = tuple()  # 不是 3.11+ 就不会进 isinstance 分支

    if eg_cls and isinstance(e, eg_cls):
        leaves: list[str] = []

        def _walk(exc: BaseException) -> None:
            sub = getattr(exc, "exceptions", None)
            if sub:
                for s in sub:
                    _walk(s)
            else:
                leaves.append(f"{type(exc).__name__}: {exc}")

        _walk(e)
        return " | ".join(leaves) if leaves else f"{type(e).__name__}: {e}"
    return f"{type(e).__name__}: {e}"


class MCPClientManager:
    """MCP 客户端管理器 (单例)."""

    def __init__(self) -> None:
        self._client: Optional[Any] = None  # MultiServerMCPClient
        self._tools: List[BaseTool] = []
        self._connected: bool = False

    # ==================== 连接管理 ====================

    async def connect(self, *, fail_silently: bool = True) -> None:
        """连接所有 MCP 服务并加载工具.

        Args:
            fail_silently: True (默认) = 失败时仅警告, 应用继续启动;
                           False = 抛异常, 阻止应用启动 (生产环境推荐)
        """
        from langchain_mcp_adapters.client import MultiServerMCPClient

        if self._connected:
            logger.debug("MCP 已连接, 跳过")
            return

        servers = self._build_connections()
        if not servers:
            logger.info("未配置 MCP 服务, 跳过 MCP 初始化")
            return

        logger.info(f"加载 MCP 服务: {list(servers.keys())}")
        try:
            self._client = MultiServerMCPClient(servers)
        except Exception as e:
            self._client = None
            if fail_silently:
                logger.warning(f"MCP 客户端初始化失败: {_format_exc(e)}")
                return
            raise

        # 逐 server 加载 (单点失败不影响其它), 单次失败重试一次
        # 重试目的: run.ps1 用 TCP 端口判 ready, 但 uvicorn 先 bind 后初始化
        # FastMCP 路由, 偶尔 handshake 撞上 warmup, 短暂 sleep 即可恢复.
        all_tools: List[BaseTool] = []
        failed: List[str] = []
        for name in servers.keys():
            tools = await self._load_one(name, retries=1, retry_delay=0.5)
            if tools is None:
                failed.append(name)
            else:
                all_tools.extend(tools)

        self._tools = all_tools
        # 只要有任意一个 server 成功就算 connected, 失败的下次启动还会重试
        self._connected = bool(all_tools) or not failed

        if all_tools:
            logger.info(
                f"已加载 {len(all_tools)} 个 MCP 工具 "
                f"(成功 {len(servers) - len(failed)}/{len(servers)} server"
                + (f", 失败: {failed}" if failed else "")
                + "):"
            )
            for tool in all_tools:
                desc = (tool.description or "").replace("\n", " ")[:80]
                logger.info(f"  - {tool.name}: {desc}")
        else:
            msg = f"未加载到任何 MCP 工具 (失败 server: {failed})"
            if fail_silently:
                logger.warning(f"{msg}, 应用以无 MCP 工具模式继续运行")
            else:
                raise RuntimeError(msg)

    async def _load_one(
        self,
        name: str,
        *,
        retries: int = 1,
        retry_delay: float = 0.5,
    ) -> Optional[List[BaseTool]]:
        """加载单个 MCP server 的工具, 失败返回 None.

        失败时把 ExceptionGroup 展开打印, 避免外层只看到
        'unhandled errors in a TaskGroup (1 sub-exception)' 这种黑盒.
        """
        assert self._client is not None
        last_err: Optional[BaseException] = None
        for attempt in range(retries + 1):
            try:
                tools = await self._client.get_tools(server_name=name)
                if attempt > 0:
                    logger.info(f"MCP '{name}' 第 {attempt + 1} 次重试成功")
                return list(tools)
            except Exception as e:  # ExceptionGroup 是 Exception 的子类, 这里能接住
                last_err = e
                if attempt < retries:
                    logger.debug(
                        f"MCP '{name}' 加载失败 (第 {attempt + 1} 次), "
                        f"{retry_delay}s 后重试: {_format_exc(e)}"
                    )
                    await asyncio.sleep(retry_delay)
        logger.warning(
            f"MCP '{name}' 加载失败 (已重试 {retries} 次): {_format_exc(last_err)}"
        )
        return None

    async def close(self) -> None:
        """清理 MCP 客户端 (mcp_adapters v0.2 是 stateless, 此处仅置空)."""
        self._client = None
        self._tools = []
        self._connected = False
        logger.info("MCP 客户端已清理")

    # ==================== 访问接口 ====================

    @property
    def tools(self) -> List[BaseTool]:
        """已加载的 MCP 工具列表 (失败时返回空列表)."""
        return self._tools

    @property
    def is_connected(self) -> bool:
        return self._connected

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """按名查找单个工具."""
        for tool in self._tools:
            if tool.name == name:
                return tool
        return None

    # ==================== 内部辅助 ====================

    @staticmethod
    def _build_connections() -> Dict[str, Dict[str, Any]]:
        """将 settings.mcp_servers 转换成 MultiServerMCPClient 期望的格式.

        v1 adapter 用 'streamable_http' (下划线), 而我们配置用 'streamable-http' (短横),
        这里做一次自动转换, 让用户配置更友好.
        """
        result: Dict[str, Dict[str, Any]] = {}
        for name, cfg in settings.mcp_servers.items():
            transport = (cfg.get("transport") or "streamable_http").replace("-", "_")
            entry: Dict[str, Any] = {"transport": transport}

            # 不同 transport 类型字段不同
            if transport in ("streamable_http", "sse"):
                if not cfg.get("url"):
                    logger.warning(f"MCP '{name}' 未配置 URL, 跳过")
                    continue
                entry["url"] = cfg["url"]
            elif transport == "stdio":
                if not cfg.get("command"):
                    logger.warning(f"MCP '{name}' 未配置 command, 跳过")
                    continue
                entry["command"] = cfg["command"]
                entry["args"] = cfg.get("args", [])
            else:
                logger.warning(f"MCP '{name}' 未知 transport: {transport}, 跳过")
                continue

            result[name] = entry
        return result


# ============================================================
# 全局单例
# ============================================================
mcp_client_manager = MCPClientManager()
