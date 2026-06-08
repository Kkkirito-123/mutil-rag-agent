import json
from typing import List, Sequence, Set

from langchain_core.tools import BaseTool, StructuredTool
from loguru import logger

from app.core.mcp_client import mcp_client_manager


def expose_tools_with_lazy_mcp(
    tools: Sequence[BaseTool],
    allowed_tool_names: Set[str],
    *,
    enabled: bool,
) -> List[BaseTool]:
    if not enabled:
        return [tool for tool in tools if tool.name in allowed_tool_names]

    mcp_tool_names = {tool.name for tool in mcp_client_manager.tools}
    direct_tools = [
        tool
        for tool in tools
        if tool.name in allowed_tool_names and tool.name not in mcp_tool_names
    ]
    lazy_mcp_allowed = allowed_tool_names & mcp_tool_names
    if lazy_mcp_allowed:
        direct_tools.extend(create_lazy_mcp_tools(lazy_mcp_allowed))
    return direct_tools


async def _invoke_mcp_tool(tool: BaseTool, arguments: dict) -> str:
    if hasattr(tool, "ainvoke"):
        result = await tool.ainvoke(arguments)
    else:
        result = tool.invoke(arguments)
    if isinstance(result, str):
        return result
    return json.dumps(result, ensure_ascii=False, default=str)


def create_lazy_mcp_tools(allowed_tool_names: Set[str]) -> List[BaseTool]:
    allowed = set(allowed_tool_names)

    async def mcp_search_tools(query: str = "") -> str:
        """搜索当前 Skill 允许调用的 MCP 工具, 用于按需发现远程工具能力.

        Args:
            query: ?????, ?? docker???????web_search?

        Returns:
            匹配的 MCP 工具清单, 包含工具名和简短描述。
        """
        query_text = (query or "").lower().strip()
        rows = []
        for tool in mcp_client_manager.tools:
            if tool.name not in allowed:
                continue
            desc = (tool.description or "").replace("\n", " ").strip()
            haystack = f"{tool.name} {desc}".lower()
            if query_text and query_text not in haystack:
                continue
            rows.append(f"- {tool.name}: {desc[:180] or '无描述'}")

        if not rows:
            return "未找到当前 Skill 允许的匹配 MCP 工具。"
        return "当前 Skill 可按需调用的 MCP 工具:\n" + "\n".join(rows)

    async def mcp_execute_tool(tool_name: str, arguments_json: str = "{}") -> str:
        """按名称执行当前 Skill 允许的 MCP 工具.

        Args:
            tool_name: 要执行的 MCP 工具名, 必须先通过 mcp_search_tools 发现。
            arguments_json: JSON 字符串形式的工具参数, 例如 {"query":"CPU 高"}。

        Returns:
            真实 MCP 工具的执行结果。
        """
        if tool_name not in allowed:
            logger.warning(f"[LazyMCP] 工具不在当前 Skill allowlist 中: {tool_name}")
            return f"Guardrails 拒绝执行 MCP 工具: {tool_name} 不在当前 Skill 允许列表中。"

        tool = mcp_client_manager.get_tool(tool_name)
        if tool is None:
            return f"未找到 MCP 工具: {tool_name}。请先调用 mcp_search_tools 确认可用工具。"

        try:
            arguments = json.loads(arguments_json or "{}")
            if not isinstance(arguments, dict):
                return "arguments_json 必须是 JSON object 字符串。"
        except json.JSONDecodeError as e:
            return f"arguments_json 不是合法 JSON: {e}"

        logger.info(f"[LazyMCP] 执行工具: {tool_name} args={arguments}")
        return await _invoke_mcp_tool(tool, arguments)

    return [
        StructuredTool.from_function(
            coroutine=mcp_search_tools,
            name="mcp_search_tools",
            description="搜索当前 Skill 允许的 MCP 工具。先用它发现工具名和用途, 再用 mcp_execute_tool 执行。",
        ),
        StructuredTool.from_function(
            coroutine=mcp_execute_tool,
            name="mcp_execute_tool",
            description="按名称执行当前 Skill 允许的 MCP 工具。tool_name 必须来自 mcp_search_tools, arguments_json 必须是 JSON object 字符串。",
        ),
    ]
