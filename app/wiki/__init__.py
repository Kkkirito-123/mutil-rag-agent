"""Karpathy LLM Wiki 模式: LLM 维护的互链 markdown 事故知识库。

取代原 append-only 经验表 (app/lessons): 诊断收尾 ingest -> LLM 合并相关页 ->
读 index 优先召回。详见 store.py 与 data/wiki/CONVENTIONS.md。
"""

from app.wiki.store import ingest_diagnosis, lint, recall_block

__all__ = ["ingest_diagnosis", "recall_block", "lint"]
