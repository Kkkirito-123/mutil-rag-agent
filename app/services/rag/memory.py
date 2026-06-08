"""RAG Chat 的会话记忆操作: query 改写 + 历史压缩."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage
from loguru import logger

from app.config import settings
from app.core.llm import get_chat_llm
from app.runtime.agent_harness import get_agent_harness
import app.services.chat_memory as chat_memory
from app.services.rag.message_utils import content_to_text, format_history


async def rewrite_question(
    question: str,
    *,
    summary: str,
    recent_messages: list[dict[str, Any]],
) -> str:
    """用历史 + summary 改写当前问题为独立检索 query, 失败回退到原文."""
    if not settings.rag_chat_memory_enabled or not settings.rag_chat_rewrite_enabled:
        return question
    if not summary and not recent_messages:
        return question
    try:
        harness = get_agent_harness()
        prompt = harness.build_rag_rewrite_prompt(
            summary=summary or "(无)",
            history=format_history(recent_messages),
            question=question,
        )
        llm = get_chat_llm(
            model=harness.rag_rewrite_model(),
            temperature=0,
            streaming=False,
            timeout=20,
            max_retries=1,
        )
        resp = await llm.ainvoke([HumanMessage(content=prompt)])
        rewritten = content_to_text(resp.content).strip().strip("\"'")
        if rewritten:
            logger.info(f"[rag] query rewrite: {question[:80]} -> {rewritten[:120]}")
            return rewritten[:1000]
    except Exception as e:
        logger.warning(f"[rag] query rewrite 失败, 使用原始问题: {type(e).__name__}: {e}")
    return question


async def compact_if_needed(session_id: str) -> None:
    """超过 max_messages 时, 把较早消息合并进 summary."""
    if not settings.rag_chat_memory_enabled or not settings.rag_chat_compact_enabled:
        return
    all_messages = await chat_memory.get_messages(session_id)
    if len(all_messages) <= settings.rag_chat_max_messages:
        return
    keep_count = max(2, settings.rag_chat_compact_keep_messages)
    old_messages = all_messages[:-keep_count]
    recent_messages = all_messages[-keep_count:]
    if not old_messages:
        return
    old_summary = await chat_memory.get_summary(session_id)
    try:
        harness = get_agent_harness()
        prompt = harness.build_rag_compact_prompt(
            max_chars=settings.rag_chat_summary_max_chars,
            old_summary=old_summary or "(无)",
            old_messages=format_history(old_messages),
        )
        llm = get_chat_llm(
            model=harness.rag_compact_model(),
            temperature=0,
            streaming=False,
            timeout=40,
            max_retries=1,
        )
        resp = await llm.ainvoke([HumanMessage(content=prompt)])
        summary = content_to_text(resp.content).strip()
        if summary:
            await chat_memory.set_summary(
                session_id, summary[: settings.rag_chat_summary_max_chars]
            )
            await chat_memory.replace_messages(session_id, recent_messages)
            logger.info(
                f"[rag] session={session_id} compact 完成: "
                f"{len(all_messages)} -> {len(recent_messages)} messages"
            )
    except Exception as e:
        logger.warning(f"[rag] compact 失败, 保留原历史: {type(e).__name__}: {e}")
