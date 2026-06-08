"""文档管理接口的数据模型."""

from typing import List

from pydantic import BaseModel, Field


class DocumentInfo(BaseModel):
    """已索引的文档元信息."""

    source: str = Field(..., description="文件名 / 来源标识")
    chunk_count: int = Field(..., description="该文档的 chunk 总数")


class DocumentListResponse(BaseModel):
    """文档列表响应."""

    total: int = Field(..., description="文档总数")
    documents: List[DocumentInfo] = Field(default_factory=list)


class UploadResponse(BaseModel):
    """文档上传响应."""

    source: str = Field(..., description="文件名")
    chunks_indexed: int = Field(..., description="索引的 chunk 数量")
    bytes: int = Field(..., description="文件字节数")


class DeleteResponse(BaseModel):
    """文档删除响应."""

    source: str = Field(..., description="被删除的文件名")
    deleted_chunks: int = Field(..., description="删除的 chunk 数量")
