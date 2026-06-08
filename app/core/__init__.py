"""核心基础设施层.

提供 LLM、Embedding、Milvus、MCP 等基础能力的统一封装.
上层 (services / agents / tools) 直接 from app.core.<module> import X,
本包不做聚合 re-export, 避免隐式 eager-import 与循环依赖.
"""
