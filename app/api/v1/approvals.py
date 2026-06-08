"""审批 API (前端审批 inbox 用)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.runtime.approvals import approval_repository

router = APIRouter(prefix="/approvals", tags=["approvals"])


class DecideRequest(BaseModel):
    decision: str = Field(..., description="approved / denied / cancelled")
    decided_by: str = Field(default="", description="操作人标识 (邮箱/用户名/'system')")
    reason: str = Field(default="", description="决策原因, 留痕用")


@router.get("/pending", summary="待审批的请求 (前端 inbox)")
async def list_pending(limit: int = 50) -> dict[str, Any]:
    try:
        items = await approval_repository.list_pending(limit=limit)
    except Exception as exc:
        # 数据库不可用时返回友好降级, 前端可以画"审批通道未就绪"
        return {"count": 0, "items": [], "available": False, "error": str(exc)}
    return {"count": len(items), "items": items, "available": True}


@router.get("/recent", summary="历史审批 (审计/复盘)")
async def list_recent(limit: int = 50) -> dict[str, Any]:
    try:
        items = await approval_repository.list_recent(limit=limit)
    except Exception as exc:
        return {"count": 0, "items": [], "available": False, "error": str(exc)}
    return {"count": len(items), "items": items, "available": True}


@router.get("/{req_id}", summary="单条审批详情")
async def get_one(req_id: str) -> dict[str, Any]:
    row = await approval_repository.get_request(req_id)
    if row is None:
        raise HTTPException(status_code=404, detail="approval not found")
    return row


@router.post("/{req_id}/decide", summary="审批: approve / deny / cancel")
async def decide(req_id: str, body: DecideRequest) -> dict[str, Any]:
    if body.decision not in ("approved", "denied", "cancelled"):
        raise HTTPException(status_code=400, detail="decision 必须是 approved / denied / cancelled")
    try:
        row = await approval_repository.decide(
            req_id,
            decision=body.decision,
            decided_by=body.decided_by,
            reason=body.reason,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"写入失败: {exc}")
    if row is None:
        raise HTTPException(status_code=409, detail="请求已被处理或不存在")
    return row
