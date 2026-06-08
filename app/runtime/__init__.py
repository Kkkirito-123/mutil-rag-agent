"""Agent 工具调用运行时 (Runtime).

子模块:
  - tool_runner: ReAct 风格的 LLM-Tool 循环, 按 ToolMeta.concurrency_safe 切批 gather 并行
  - tool_filter: 按 Skill allowed_tools + PermissionMode 过滤工具集
  - permissions: allow / ask / deny 三态权限决策
  - transitions: 显式状态转换记录

设计原则:
  - Runtime 层只依赖 tools / skills / config, 不依赖 agents/diagnosis 节点
  - 调用方直接 from app.runtime.<sub> import ..., 本包不做 re-export 避免循环依赖
"""
