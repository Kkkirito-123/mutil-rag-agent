"""LLM 工厂.

统一管理 Chat 模型的创建. 所有上层模块 (planner/executor/replanner/services)
都应通过 get_chat_llm() 获取 LLM, 不要直接 new ChatOpenAI.

设计要点:
  - 使用 DashScope 的 OpenAI 兼容模式, 直接复用 langchain_openai.ChatOpenAI
  - 默认参数集中在此, 修改 LLM 行为只需改这一处
  - 不做 lru_cache: 每次调用返回新实例 (因为 temperature/streaming 等参数因调用方而异)
"""

from typing import Any, Optional

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from loguru import logger

from app.config import settings
from app.core.llm_health import is_primary_llm_available


def _requires_disable_thinking_for_non_streaming(model_name: str) -> bool:
    normalized = model_name.lower()
    return any(token in normalized for token in ("qwen3", "qwq", "qvq"))


def _should_use_local_llm() -> bool:
    """决定本次调用是否走本地 LLM.

    优先级:
      1. local_llm_force=True → 强制本地 (调试/离线开发专用)
      2. dashscope_api_key 为空 / 不合法 → 本地
      3. local_llm_enabled 且主 LLM TCP 探测不可达 → 本地
      4. 其他 → 主 LLM (DashScope)
    """
    if not settings.local_llm_enabled and not settings.local_llm_force:
        return False
    if settings.local_llm_force:
        return True
    api_key = (settings.dashscope_api_key or "").strip()
    if not api_key or api_key.startswith("sk-your"):
        return True
    return not is_primary_llm_available()


def _build_local_llm(
    *, temperature: float, streaming: bool, timeout: Optional[float], **kwargs: Any
) -> BaseChatModel:
    """创建本地 LLM 实例 (走 Ollama 的 OpenAI 兼容接口)."""
    return ChatOpenAI(
        model=settings.local_llm_model,
        api_key=settings.local_llm_api_key or "ollama",  # type: ignore[arg-type]
        base_url=settings.local_llm_base_url,
        temperature=temperature,
        streaming=streaming,
        timeout=timeout,
        max_retries=1,  # 本地环境不需多次重试
        **kwargs,
    )


def get_chat_llm(
    *,
    model: Optional[str] = None,
    temperature: float = 0.0,
    streaming: bool = False,
    timeout: Optional[float] = 60.0,
    max_retries: int = 2,
    **kwargs: Any,
) -> BaseChatModel:
    """获取 Chat 模型实例.

    Args:
        model: 模型名 (None 则用 settings.dashscope_chat_model)
        temperature: 采样温度 (0 = 确定性, 适合 Planner; 0.7 = 创造性, 适合生成报告)
        streaming: 是否流式输出 (SSE 场景需开启)
        timeout: 超时秒数
        max_retries: 失败重试次数
        **kwargs: 传给 ChatOpenAI 的额外参数

    Returns:
        BaseChatModel 实例

    Examples:
        >>> # Planner 用 (确定性)
        >>> llm = get_chat_llm(temperature=0)
        >>>
        >>> # Replanner 流式生成报告
        >>> llm = get_chat_llm(temperature=0.3, streaming=True)
    """
    # ===== 断网 / 未配置 API key 时回退本地 LLM =====
    if _should_use_local_llm():
        logger.info(
            f"[LLM] 使用本地 LLM: {settings.local_llm_model} "
            f"@ {settings.local_llm_base_url} (force={settings.local_llm_force})"
        )
        # 本地模型不需要 enable_thinking 参数 (那个是 DashScope Qwen3 专用)
        kwargs.pop("extra_body", None)
        return _build_local_llm(
            temperature=temperature,
            streaming=streaming,
            timeout=timeout,
            **kwargs,
        )

    selected_model = model or settings.dashscope_chat_model

    # 模型名以 deepseek 开头 → 路由到 DeepSeek (OpenAI 兼容).
    # DeepSeek v4 默认开思考模式, 会在 assistant message 里返回 reasoning_content,
    # 下一轮请求必须把 reasoning_content 原样回传, 否则 400:
    #   "The reasoning_content in the thinking mode must be passed back to the API."
    # Agent tool loop 不维护 reasoning_content, 所以这里**默认关掉思考模式**.
    # 想开的话, 调 get_chat_llm 时传 extra_body={"thinking": {"type": "enabled"}}.
    if selected_model.lower().startswith("deepseek"):
        ds_extra = kwargs.pop("extra_body", None) or {}
        if not isinstance(ds_extra, dict):
            ds_extra = {}
        ds_extra.pop("enable_thinking", None)  # DashScope 专属, DeepSeek 不吃
        ds_extra.setdefault("thinking", {"type": "disabled"})
        kwargs["extra_body"] = ds_extra
        # DeepSeek 也是 OpenAI 兼容, 流式时让最后一帧带回真实 usage
        # (input_tokens / output_tokens / total_tokens / prompt_cache_hit_tokens 等).
        # LangChain ChatOpenAI 的 stream_usage=True 会被翻译成
        #   stream_options={"include_usage": True}, 与官方文档一致.
        if streaming:
            kwargs.setdefault("stream_usage", True)
        api_key = (settings.deepseek_api_key or "").strip()
        if not api_key:
            logger.warning(
                "[LLM] 选择 DeepSeek 模型但 DEEPSEEK_API_KEY 未配置, 仍尝试调用 (会 401)"
            )
        return ChatOpenAI(
            model=selected_model,
            api_key=api_key or "missing",  # type: ignore[arg-type]
            base_url=settings.deepseek_base_url,
            temperature=temperature,
            streaming=streaming,
            timeout=timeout,
            max_retries=max_retries,
            **kwargs,
        )

    # ===== DashScope (默认) =====
    if not streaming and _requires_disable_thinking_for_non_streaming(selected_model):
        extra_body = kwargs.get("extra_body") or {}
        if isinstance(extra_body, dict):
            kwargs["extra_body"] = {**extra_body, "enable_thinking": False}

    # 流式时让最后一帧携带 usage (input_tokens/output_tokens/total_tokens)
    if streaming:
        kwargs.setdefault("stream_usage", True)

    return ChatOpenAI(
        model=selected_model,
        api_key=settings.dashscope_api_key,  # type: ignore[arg-type]
        base_url=settings.dashscope_base_url,
        temperature=temperature,
        streaming=streaming,
        timeout=timeout,
        max_retries=max_retries,
        **kwargs,
    )
