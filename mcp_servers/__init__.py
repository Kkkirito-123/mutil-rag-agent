"""MCP 工具服务 (独立进程).

每个文件是一个独立的 MCP server, 通过 streamable-http transport 暴露工具.
被 multi_agent 主应用通过 langchain_mcp_adapters 远程调用.

启动:
  python mcp_servers/log_server.py       # 端口 8003
  python mcp_servers/monitor_server.py   # 端口 8004
"""
