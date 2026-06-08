"""评估结果只读 API.

把 benchmark/reports/ 下的 retrieval / ragas 报告暴露给前端, 让"检索质量"
可视化, 不再只能 cat JSON. 这是 RAG 半边产品化的关键差异点.

约定: 报告文件名形如 `<mode>_YYYYMMDD-HHMMSS.json`, 由 benchmark/run_benchmark.py 写入.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/eval", tags=["eval"])

REPORTS_DIR = Path(__file__).resolve().parents[3] / "benchmark" / "reports"
MERGED_REPORTS_FILE = REPORTS_DIR / "merged_reports.json"

# 文件名约定: retrieval_20260605-141501.json / ragas_20260605-130000.json
_FILENAME_RE = re.compile(r"^(?P<mode>[a-z_]+)_(?P<ts>\d{8}-\d{6})\.json$")


def _validate_filename(name: str) -> None:
    """限制只能读 reports 目录下的文件名, 防路径穿越."""
    if "/" in name or "\\" in name or ".." in name:
        raise HTTPException(status_code=400, detail="非法文件名")


def _load_merged_reports() -> dict[str, dict[str, Any]]:
    """把 GitHub 友好的合并包展开为只读虚拟报告。"""
    if not MERGED_REPORTS_FILE.is_file():
        return {}
    try:
        merged = json.loads(MERGED_REPORTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

    reports: dict[str, dict[str, Any]] = {}
    for item in merged.get("reports") or []:
        if not isinstance(item, dict):
            continue
        source = item.get("source") or {}
        name = str(source.get("file") or "")
        payload = item.get("data")
        if _FILENAME_RE.match(name) and isinstance(payload, dict):
            reports[name] = payload
    return reports


def _load_report(name: str) -> dict[str, Any]:
    _validate_filename(name)
    path = REPORTS_DIR / name
    if path.is_file() and name != MERGED_REPORTS_FILE.name:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"读取失败: {exc}") from exc

    payload = _load_merged_reports().get(name)
    if payload is None:
        raise HTTPException(status_code=404, detail="report not found")
    return payload


def _parse_ts(ts: str) -> str:
    """20260605-141501 → ISO8601, 解析失败原样返回."""
    try:
        return datetime.strptime(ts, "%Y%m%d-%H%M%S").isoformat()
    except Exception:
        return ts


def _summarize(payload: dict[str, Any]) -> dict[str, Any]:
    """从完整报告里挑高价值字段做列表摘要, 不返回 details (可能几 MB)."""
    mode = payload.get("mode", "")
    summary: dict[str, Any] = {
        "mode": mode,
        "rows": payload.get("rows"),
        "elapsed_sec": payload.get("elapsed_sec"),
    }
    if mode == "retrieval":
        summary.update({
            "k": payload.get("k"),
            "hit_at_k": payload.get("hit_at_k"),
            "mrr_at_k": payload.get("mrr_at_k"),
            "recall_at_k": payload.get("recall_at_k"),
            "hybrid": payload.get("hybrid"),
            "rerank": payload.get("rerank"),
        })
    elif mode == "ragas":
        averages = payload.get("averages") or {}
        oe = payload.get("openevals_averages") or {}
        summary.update({
            "faithfulness": averages.get("faithfulness"),
            "answer_relevancy": averages.get("answer_relevancy"),
            "context_precision": averages.get("context_precision"),
            "context_recall": averages.get("context_recall"),
            "groundedness": oe.get("groundedness"),
            "helpfulness": oe.get("helpfulness"),
        })
    return summary


@router.get("/reports", summary="列出最近评估报告")
async def list_reports(
    limit: int = Query(20, ge=1, le=200),
    mode: str | None = Query(None, description="可选: 只列某种模式 (retrieval / ragas)"),
) -> dict[str, Any]:
    """按 mtime 倒序返回报告概览, 不含 details (太大)."""
    if not REPORTS_DIR.exists():
        return {"count": 0, "items": [], "reports_dir": str(REPORTS_DIR), "note": "目录不存在, 先运行 benchmark/run_benchmark.py"}

    payloads = _load_merged_reports()
    for path in REPORTS_DIR.glob("*.json"):
        if path.name == MERGED_REPORTS_FILE.name or not _FILENAME_RE.match(path.name):
            continue
        try:
            payloads[path.name] = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

    items: list[dict[str, Any]] = []
    for name in sorted(payloads, reverse=True):
        m = _FILENAME_RE.match(name)
        if not m:
            continue
        file_mode = m.group("mode")
        if mode and file_mode != mode:
            continue
        payload = payloads[name]
        items.append({
            "name": name,
            "mode": file_mode,
            "generated_at": _parse_ts(m.group("ts")),
            "size_bytes": len(json.dumps(payload, ensure_ascii=False).encode("utf-8")),
            "summary": _summarize(payload),
        })
        if len(items) >= limit:
            break
    return {"count": len(items), "items": items, "reports_dir": str(REPORTS_DIR)}


@router.get("/reports/{name}", summary="读取某份评估报告")
async def get_report(name: str, include_details: bool = Query(False)) -> dict[str, Any]:
    """默认剥掉 details 以便前端快速渲染, include_details=true 时返回完整 JSON."""
    payload = _load_report(name)
    if include_details:
        return payload
    # 默认裁掉 details (avoid 几 MB), 给前端"按需展开"的能力
    light = {k: v for k, v in payload.items() if k != "details"}
    light["details_count"] = len(payload.get("details") or [])
    return light


@router.get("/reports/{name}/low-scores", summary="挑出低分题 (用于补语料)")
async def list_low_scores(
    name: str,
    threshold: float = Query(0.5, ge=0.0, le=1.0),
    metric: str = Query("faithfulness", description="ragas 指标: faithfulness / answer_relevancy / context_precision / context_recall"),
    limit: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """从 ragas 报告里挑分数低于 threshold 的样本, 直接告诉你"补哪些语料".

    retrieval 报告则按 hit=0 (MISS) 挑.
    """
    payload = _load_report(name)
    details = payload.get("details") or []
    mode = payload.get("mode")
    out: list[dict[str, Any]] = []
    if mode == "ragas":
        for row in details:
            score = (row.get("scores") or {}).get(metric)
            if score is None:
                continue
            if score <= threshold:
                out.append({
                    "id": row.get("id"),
                    "scenario": row.get("scenario"),
                    "question": row.get("question"),
                    "answer": (row.get("answer") or "")[:300],
                    "score": score,
                    "all_scores": row.get("scores"),
                })
    elif mode == "retrieval":
        for row in details:
            score = (row.get("score") or {}).get("hit", 0.0)
            if score < 0.5:
                out.append({
                    "id": row.get("id"),
                    "scenario": row.get("scenario"),
                    "query": row.get("query"),
                    "score": row.get("score"),
                    "hits_top": (row.get("hits") or [])[:3],
                })
    out.sort(key=lambda x: (x.get("score") if isinstance(x.get("score"), (int, float)) else 0.0))
    return {"mode": mode, "metric": metric if mode == "ragas" else "hit", "threshold": threshold, "count": len(out), "items": out[:limit]}
