"""RAG 工具函数: 消息格式化."""

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage


def content_to_text(content: Any) -> str:
    """LangChain 消息 content 可能是 str 或 list[dict|str], 统一抽成纯文本."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            c.get("text", "") if isinstance(c, dict) else str(c) for c in content
        )
    return str(content)


def format_history(messages: list[dict[str, Any]]) -> str:
    """把 [{role, content}, ...] 渲染成给 prompt 看的多行文本."""
    if not messages:
        return "(无)"
    lines = []
    for item in messages:
        role = "用户" if item.get("role") == "user" else "助手"
        content = str(item.get("content") or "").strip()
        if content:
            lines.append(f"{role}: {content[:1200]}")
    return "\n".join(lines) if lines else "(无)"


def history_to_messages(messages: list[dict[str, Any]]) -> list[HumanMessage | AIMessage]:
    """把字典历史转成 LangChain Message 列表."""
    converted: list[HumanMessage | AIMessage] = []
    for item in messages:
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        if item.get("role") == "user":
            converted.append(HumanMessage(content=content[:2000]))
        elif item.get("role") == "assistant":
            converted.append(AIMessage(content=content[:3000]))
    return converted
