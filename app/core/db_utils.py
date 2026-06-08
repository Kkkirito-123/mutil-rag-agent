"""Repository 层共享的小工具.

聚合点: 此前 ``_json`` / ``_new_id`` 在 incidents / evidence / orchestration /
knowledge_graph / reflection 五个 repository 各自重复定义. 抽到此处统一.

``json_dump`` 采用 ``reflection.repository`` 的安全版本: 显式判 ``None``,
不写 ``data or {}`` —— 否则空 list ``[]`` 会被 falsy 化成 ``{}``, 破坏 JSONB
数组列.
"""

from __future__ import annotations

import json
import uuid
from typing import Any


def json_dump(data: Any) -> str:
    """安全序列化为 JSONB 写入用的字符串."""
    if data is None:
        data = {}
    return json.dumps(data, ensure_ascii=False, default=str)


def new_id(prefix: str) -> str:
    """生成 ``<prefix>_<uuid4 hex>`` 形式的实体 id."""
    return f"{prefix}_{uuid.uuid4().hex}"
