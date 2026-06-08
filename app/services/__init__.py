"""业务服务层.

每个 service 封装一类业务逻辑, 是 API 层和 core/agents 层之间的协调者.
调用方请直接 import 具体 service 模块, 本包不做 re-export, 避免链式 eager 加载.
"""
