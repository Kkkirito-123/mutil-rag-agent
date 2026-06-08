"""时间工具.

给 Agent 用. 因为 LLM 训练时间固定, 不知道"当前"时间.
诊断报告里需要写时间戳时, 必须用这个工具拿真实时间.
"""

from datetime import datetime
from typing import Optional

from langchain_core.tools import tool


@tool
def get_current_time(timezone: Optional[str] = None) -> str:
    """获取当前时间.

    在生成诊断报告 / 记录事件时间戳时调用.

    Args:
        timezone: 时区 (暂不实现, 默认本地时区)

    Returns:
        ISO 8601 格式的时间字符串, 如 "2026-04-26T10:30:45+08:00"
    """
    now = datetime.now().astimezone()
    return now.isoformat(timespec="seconds")
