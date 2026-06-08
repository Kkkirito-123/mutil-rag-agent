"""结构化输出兼容层.

统一使用 response_format={"type": "json_object"} + Pydantic 校验, 避免部分
OpenAI 兼容接口不支持 SDK Pydantic parse response_format.
"""

from __future__ import annotations

from typing import TypeVar

from langchain_core.language_models import BaseChatModel
from loguru import logger
from pydantic import BaseModel

from app.core.llm_parse import extract_json

T = TypeVar("T", bound=BaseModel)


def is_deepseek_model(model: str | None) -> bool:
    return bool((model or "").lower().startswith("deepseek"))


def _schema_hint(schema_cls: type[BaseModel]) -> str:
    schema = schema_cls.model_json_schema()
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    lines = []
    for name, meta in props.items():
        type_name = meta.get("type") or meta.get("anyOf") or "any"
        req = "必填" if name in required else "可选"
        desc = meta.get("description", "")
        lines.append(f'- "{name}" ({req}, {type_name}): {desc}')
    return "\n".join(lines)


async def ainvoke_structured(
    *,
    llm: BaseChatModel,
    schema_cls: type[T],
    messages: list[dict[str, str]],
    model_name: str | None,
) -> T:
    """调用 LLM 并返回 Pydantic 对象.

    所有模型统一走 JSON 文本解析, 避免部分 OpenAI 兼容接口不支持 SDK Pydantic parse.
    """
    # 注意: DashScope 兼容接口对 response_format=json_object 有一个硬约束 —
    # messages 里必须出现**小写** "json" 字样, 否则返回 400
    #   "messages must contain the word 'json' in some form".
    # OpenAI 官方校验是大小写不敏感的, DashScope 的实现更严, 这里统一用小写, 并多写几次保险.
    json_instruction = {
        "role": "system",
        "content": (
            "你必须只输出一个合法的 json 对象 (严格 json 格式, 小写 json), "
            "不要 markdown, 不要代码块, 不要解释。\n"
            "json 字段要求:\n"
            f"{_schema_hint(schema_cls)}"
        ),
    }

    json_llm = llm.bind(response_format={"type": "json_object"})
    resp = await json_llm.ainvoke([json_instruction, *messages])
    content = getattr(resp, "content", resp)
    if isinstance(content, list):
        text = "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in content
        )
    else:
        text = str(content)
    data = extract_json(text, source="structured output")
    obj = schema_cls.model_validate(data)
    logger.debug(f"[structured] JSON parsed as {schema_cls.__name__}: {obj}")
    return obj
