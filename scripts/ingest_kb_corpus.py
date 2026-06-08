"""批量入库脚本: docs/ + data/kb_corpus/ -> Milvus.

用途:
  - 把 docs/ 下的 OnCall SOP 和 data/kb_corpus/ 下的开源告警语料
    切分 -> embedding -> 写入 Milvus
  - 走和线上 RAG 一致的链路: split_markdown() + get_vector_store().add_documents()
  - 失败的文件单独记录, 不影响其他文件入库

用法:
  python scripts/ingest_kb_corpus.py             # 入库
  python scripts/ingest_kb_corpus.py --dry-run   # 只切分不入库, 看会有多少 chunks
  python scripts/ingest_kb_corpus.py --reset     # 先 drop 老 collection 再入库
  python scripts/ingest_kb_corpus.py --limit 50  # 只入前 50 个文件 (调试用)

前置条件:
  - Milvus 已启动 (docker-compose up -d)
  - DASHSCOPE_API_KEY 已配置
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import List, Tuple

# 让脚本能从仓库根目录导入 app.*
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from langchain_core.documents import Document  # noqa: E402
from loguru import logger  # noqa: E402

DOCS_DIR = ROOT / "docs" / "sop"
KB_CORPUS_DIR = ROOT / "data" / "kb_corpus"
ALLOWED_DOCS = ["redis_oncall_sop.md", "mysql_oncall_sop.md", "common_alerts.md"]
CHECKPOINT_PATH = ROOT / "data" / ".ingest_checkpoint.json"


def collect_files(limit: int = 0) -> List[Tuple[Path, str]]:
    """扫描所有要入库的 (文件路径, source 标识)."""
    files: List[Tuple[Path, str]] = []

    # docs/ 下指定的 SOP 文档
    for fname in ALLOWED_DOCS:
        p = DOCS_DIR / fname
        if p.exists():
            files.append((p, fname))

    # data/kb_corpus/ 下递归所有 .md
    if KB_CORPUS_DIR.exists():
        for p in sorted(KB_CORPUS_DIR.rglob("*.md")):
            rel = p.relative_to(KB_CORPUS_DIR).as_posix()
            files.append((p, rel))

    if limit > 0:
        files = files[:limit]
    return files


def split_all(files: List[Tuple[Path, str]]) -> List[Document]:
    """把所有文件切成 Document chunks."""
    from app.core.splitter import split_markdown

    all_chunks: List[Document] = []
    failed = 0
    for fpath, source in files:
        try:
            content = fpath.read_text(encoding="utf-8")
            chunks = split_markdown(content, source=source)
            all_chunks.extend(chunks)
        except Exception as e:
            failed += 1
            logger.warning(f"切分失败: {fpath} -> {e}")
    logger.info(
        f"切分完成: {len(files)} 文件 -> {len(all_chunks)} chunks (失败 {failed})"
    )
    return all_chunks


def _chunks_fingerprint(chunks: List[Document]) -> str:
    """为本次切分结果生成稳定指纹, 防止拿旧 checkpoint 续跑到另一批数据上。"""
    h = hashlib.sha256()
    for c in chunks:
        meta = c.metadata or {}
        h.update(str(meta.get("source") or "").encode("utf-8"))
        h.update(b"\0")
        h.update(str(meta.get("chunk_index") or "").encode("utf-8"))
        h.update(b"\0")
        h.update(c.page_content.encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()


def _load_checkpoint(dataset_hash: str, batch_size: int) -> int:
    if not CHECKPOINT_PATH.exists():
        return 0
    try:
        data = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return 0
    if data.get("dataset_hash") != dataset_hash:
        logger.warning("checkpoint 指纹不匹配, 从头开始")
        return 0
    if int(data.get("batch_size") or 0) != batch_size:
        logger.warning("checkpoint batch_size 不匹配, 从头开始")
        return 0
    return max(0, int(data.get("next_index") or 0))


def _save_checkpoint(dataset_hash: str, batch_size: int, next_index: int, total: int) -> None:
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_PATH.write_text(
        json.dumps(
            {
                "dataset_hash": dataset_hash,
                "batch_size": batch_size,
                "next_index": next_index,
                "total": total,
                "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _clear_checkpoint() -> None:
    if CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()


def ingest_to_milvus(chunks: List[Document], batch_size: int = 100, resume: bool = False) -> None:
    """分批写入 Milvus."""
    from app.core.vector_store import get_vector_store

    vs = get_vector_store()
    total = len(chunks)
    dataset_hash = _chunks_fingerprint(chunks)
    start_index = _load_checkpoint(dataset_hash, batch_size) if resume else 0
    start_index = min(start_index, total)
    logger.info(
        f"开始入库: {total} chunks, batch_size={batch_size}, "
        f"resume={resume}, start_index={start_index}"
    )

    t0 = time.perf_counter()
    written = start_index
    failed_batches = 0
    consecutive_failures = 0
    max_retries = 2
    for i in range(start_index, total, batch_size):
        batch = chunks[i : i + batch_size]
        for attempt in range(1, max_retries + 2):
            try:
                vs.add_documents(batch)
                written += len(batch)
                _save_checkpoint(dataset_hash, batch_size, i + len(batch), total)
                consecutive_failures = 0
                elapsed = time.perf_counter() - t0
                rate = written / max(elapsed, 0.01)
                eta = (total - written) / max(rate, 0.01)
                logger.info(
                    f"  进度 {written}/{total} ({100*written/total:.1f}%), "
                    f"速率 {rate:.1f} chunk/s, 剩余 {eta:.0f}s"
                )
                break
            except Exception as e:
                if attempt <= max_retries:
                    logger.warning(
                        f"  batch [{i}:{i+len(batch)}] 第 {attempt} 次失败, "
                        f"重连后重试: {type(e).__name__}: {e}"
                    )
                    get_vector_store.cache_clear()
                    time.sleep(min(5, attempt * 2))
                    vs = get_vector_store()
                    continue

                failed_batches += 1
                consecutive_failures += 1
                logger.error(f"  batch [{i}:{i+len(batch)}] 失败: {type(e).__name__}: {e}")
                if consecutive_failures >= 3:
                    raise RuntimeError(
                        "Milvus 连续 3 个 batch 写入失败, 已停止入库. "
                        "请先检查 docker compose ps standalone / docker logs multi-agent-milvus."
                    ) from e

    elapsed = time.perf_counter() - t0
    logger.info(f"入库完成: {written}/{total}, 失败 batch={failed_batches}, 总耗时 {elapsed:.1f}s")
    if failed_batches:
        raise RuntimeError(f"入库存在失败 batch={failed_batches}, 请修复后重跑 --reset")
    if written >= total:
        logger.info("入库完整完成, 清理 checkpoint")
        _clear_checkpoint()


def reset_collection() -> None:
    """drop 旧的 collection (慎用)."""
    from pymilvus import MilvusClient

    from app.config import settings

    uri = f"http://{settings.milvus_host}:{settings.milvus_port}"
    client = MilvusClient(uri=uri)
    if client.has_collection(settings.milvus_collection):
        client.drop_collection(settings.milvus_collection)
        logger.info(f"已 drop collection: {settings.milvus_collection}")
    else:
        logger.info(f"collection 不存在, 跳过 drop: {settings.milvus_collection}")
    # 清掉单例缓存, 让下次 get_vector_store 重建
    from app.core.vector_store import get_vector_store

    get_vector_store.cache_clear()


def main() -> None:
    parser = argparse.ArgumentParser(description="批量入库 docs/ + kb_corpus/ -> Milvus")
    parser.add_argument("--dry-run", action="store_true", help="只切分不入库")
    parser.add_argument("--reset", action="store_true", help="先 drop 老 collection")
    parser.add_argument("--resume", action="store_true", help="从上次成功 batch 的 checkpoint 续跑")
    parser.add_argument("--limit", type=int, default=0, help="只入前 N 个文件 (0=全部)")
    parser.add_argument("--batch", type=int, default=100, help="每批入库 chunk 数")
    args = parser.parse_args()

    # 加载 .env (拿 DASHSCOPE_API_KEY / MILVUS_HOST 等)
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ImportError:
        pass

    files = collect_files(limit=args.limit)
    logger.info(f"扫描到 {len(files)} 个 .md 文件")
    if not files:
        logger.error("没有找到任何文件, 请确认 docs/ 和 data/kb_corpus/ 下有 .md")
        sys.exit(1)

    chunks = split_all(files)
    if not chunks:
        logger.error("切分后 0 个 chunk, 退出")
        sys.exit(1)

    avg_len = sum(len(c.page_content) for c in chunks) / len(chunks)
    logger.info(
        f"切分统计: {len(chunks)} chunks, 平均 {avg_len:.0f} 字, "
        f"预计入库耗时 {len(chunks)/30:.0f}-{len(chunks)/15:.0f}s"
    )

    if args.dry_run:
        logger.info("dry-run 模式, 不入库. 示例 chunk:")
        for c in chunks[:3]:
            logger.info(f"  source={c.metadata.get('source')}")
            logger.info(f"  chapter={c.metadata.get('chapter')}")
            logger.info(f"  content[:120]={c.page_content[:120]!r}")
            logger.info("  ---")
        return

    if args.reset and args.resume:
        logger.error("--reset 和 --resume 不能同时使用: reset 会删除旧 collection, resume 需要保留旧数据")
        sys.exit(1)

    if args.reset:
        _clear_checkpoint()
        reset_collection()

    ingest_to_milvus(chunks, batch_size=args.batch, resume=args.resume)


if __name__ == "__main__":
    main()
