"""LangChain Tools.

包含两类工具:
  - 本地工具 (knowledge_tool, time_tool, system_tool): 进程内执行
  - MCP 工具 (日志 / 监控 / 系统 / 通知): 通过 mcp_client_manager 远程加载

调用方请直接 from app.tools.<module> import ..., 本包不做 re-export,
避免在 import 包时触发 system_tool / mcp_loader 等模块的副作用 (psutil 等).
"""
