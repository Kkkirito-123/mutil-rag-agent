"""文档管理接口.

POST   /api/v1/documents/upload    上传单个 .md/.txt 并自动建索引
GET    /api/v1/documents           列出已索引文档
DELETE /api/v1/documents/{source}  按文件名删除文档
"""

import secrets

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status

from app.config import settings
from app.schemas.common import ApiResponse
from app.schemas.document import DeleteResponse, DocumentListResponse, UploadResponse
import app.services.document_service as document_service

router = APIRouter(prefix="/documents", tags=["documents"])


def require_kb_admin_token(
    x_kb_admin_token: str = Header(default="", alias="X-KB-Admin-Token"),
) -> None:
    expected = settings.kb_admin_token.strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="知识库写操作已锁定, 请先配置 KB_ADMIN_TOKEN",
        )
    if not secrets.compare_digest(x_kb_admin_token, expected):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限执行知识库写操作",
        )


@router.post(
    "/upload",
    response_model=ApiResponse[UploadResponse],
    summary="上传文档并建索引",
    description=(
        "上传 Markdown (`.md`/`.markdown`) 或纯文本 (`.txt`) 文件, "
        "服务端会自动: 按 H1/H2/H3 切分章节 → 大块再按字符数细切 → "
        "向量化 → 写入 Milvus."
    ),
    dependencies=[Depends(require_kb_admin_token)],
)
async def upload(file: UploadFile = File(..., description="待索引的文件")) -> ApiResponse[UploadResponse]:
    result = await document_service.upload_document(file)
    return ApiResponse.success(data=result, message=f"已索引 {result.chunks_indexed} 块")


@router.get(
    "",
    response_model=ApiResponse[DocumentListResponse],
    summary="文档列表",
)
async def list_documents() -> ApiResponse[DocumentListResponse]:
    docs = document_service.list_documents()
    return ApiResponse.success(
        data=DocumentListResponse(total=len(docs), documents=docs)
    )


@router.delete(
    "/{source}",
    response_model=ApiResponse[DeleteResponse],
    summary="删除文档",
    description="按文件名 (source) 删除该文档对应的所有 chunks",
    dependencies=[Depends(require_kb_admin_token)],
)
async def delete_document(source: str) -> ApiResponse[DeleteResponse]:
    deleted = document_service.delete_document(source)
    return ApiResponse.success(
        data=DeleteResponse(source=source, deleted_chunks=deleted),
        message=f"已删除 {deleted} 个 chunk",
    )
