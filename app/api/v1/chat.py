"""RAG 聊天接口 (流式 SSE).

POST /api/v1/chat/stream
  -> 接收 ChatRequest (session_id, question, top_k)
  -> 返回 SSE 事件流, 每个事件是 {"type": "token"|"end"|"error", "content": "..."}
  -> 前端用 EventSource 接收, 拼接 token 渲染
"""

import json
from typing import AsyncIterator

from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

import app.services.chat_memory as chat_memory
import app.services.rag_service as rag_service

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """RAG 聊天请求。"""

    session_id: str = Field(default="default", description="会话 ID, 用于多轮对话")
    question: str = Field(..., description="用户问题", min_length=1, max_length=2000)
    top_k: int | None = Field(
        default=None,
        description="可选: 覆盖知识库返回片段数; 不填则按 RAG_TOP_K 默认值",
        ge=1,
        le=20,
    )
    web_search: bool = Field(default=False, description="是否启用受限联网搜索补充资料")
    mcp_tools: bool = Field(default=True, description="是否允许 RAG Chat 调用 MCP 只读工具")

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "session-001",
                "question": "Redis 内存使用率过高怎么处理?",
                "web_search": False,
                "mcp_tools": True,
            }
        }
    }


@router.post(
    "/stream",
    summary="RAG 流式聊天",
    description=(
        "基于知识库的 RAG 单智能体聊天, SSE 流式输出.\n\n"
        "**事件格式** (event=message):\n"
        "```json\n"
        '{"type": "token", "content": "回答的某一段文本"}\n'
        '{"type": "end"}                    // 流结束\n'
        '{"type": "error", "message": "..."}\n'
        "```\n\n"
        "**前端示例**:\n"
        "```javascript\n"
        "const resp = await fetch('/api/v1/chat/stream', {method: 'POST', body: ...});\n"
        "const reader = resp.body.getReader();\n"
        "// ... 读取并拼接 token\n"
        "```"
    ),
)
async def chat_stream(req: ChatRequest) -> EventSourceResponse:
    logger.info(f"[chat] session={req.session_id}, q={req.question[:60]}...")

    async def event_generator() -> AsyncIterator[dict]:
        try:
            async for event in rag_service.stream_chat(
                req.question,
                session_id=req.session_id,
                top_k=req.top_k,
                web_search=req.web_search,
                mcp_tools=req.mcp_tools,
            ):
                # 向后兼容: 若底层 yield 的是字符串, 默认当 token 包装
                if isinstance(event, str):
                    event = {"type": "token", "content": event}
                yield {
                    "event": "message",
                    "data": json.dumps(event, ensure_ascii=False),
                }
            yield {"event": "message", "data": json.dumps({"type": "end"})}

        except Exception as e:
            logger.exception(f"[chat] stream 异常: {e}")
            yield {
                "event": "message",
                "data": json.dumps(
                    {"type": "error", "message": str(e)}, ensure_ascii=False
                ),
            }

    return EventSourceResponse(event_generator())


@router.get(
    "/sessions/{session_id}/history",
    summary="查看 RAG Chat 会话历史",
    description="返回 Redis 中保存的会话摘要与最近消息。Redis 未启用或不可用时返回空历史。",
)
async def get_chat_history(session_id: str) -> dict:
    session = await chat_memory.load_session(session_id)
    return {
        "session_id": session_id,
        "memory_enabled": await chat_memory.is_available(),
        "summary": session.get("summary") or "",
        "messages": session.get("messages") or [],
    }


@router.delete(
    "/sessions/{session_id}",
    summary="清空 RAG Chat 会话记忆",
    description="删除指定 session_id 的 Redis 会话摘要与消息历史。",
)
async def clear_chat_session(session_id: str) -> dict:
    cleared = await chat_memory.clear_session(session_id)
    return {"session_id": session_id, "cleared": cleared}
