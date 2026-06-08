"""知识库检索工具 (RAG Tool).

Agent 拿到这个工具, 可以查询运维知识库 (上传的 SOP 文档、On-Call 手册等).
返回 top-k 相关片段 + 元数据 (来源、章节).

设计要点:
  - 使用 @tool 装饰器, LangChain 会自动从函数签名 + docstring 生成 schema
  - 描述要写得清楚: LLM 决定何时调用工具完全靠 description
  - 返回字符串 (不是 dict), 因为 Agent 把工具返回值当 ToolMessage 内容
  - 失败兜底: collection 不存在/Milvus 挂了 → 返回友好提示, 不抛异常
"""

from langchain_core.tools import tool
from loguru import logger

from app.rag.retrieval import build_context


@tool
async def search_knowledge_base(query: str) -> str:
    """搜索运维知识库 (SOP、On-Call 手册、故障处理流程等).

    在以下场景调用本工具:
    - 需要查询某种告警的标准处理流程
    - 需要参考已有的故障处理经验
    - 需要确认特定服务的架构或依赖
    - 需要查找运维规范、配置项说明

    Args:
        query: 查询关键词或问题, 例如 "CPU 100% 怎么处理" 或 "MySQL 主从同步异常"

    Returns:
        相关文档片段 (Markdown 格式), 包含来源信息. 如果没有匹配返回提示信息.
    """
    context, hits, _sources, _hits_meta = await build_context(query)

    if hits <= 0:
        logger.info(f"[knowledge_tool] 无匹配: query={query!r}")
        return (
            f"知识库中没有找到与 '{query}' 直接相关的文档。"
            f"请尝试换个关键词搜索, 或基于已有经验给出建议。"
        )

    logger.info(f"[knowledge_tool] 命中 {hits} 篇: query={query!r}")

    return context
