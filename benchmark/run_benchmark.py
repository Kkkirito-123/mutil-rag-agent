"""Realtime benchmark runner for retrieval R@K and RAGAS.

Examples:
  python benchmark/run_benchmark.py retrieval --k 3
  python benchmark/run_benchmark.py retrieval --scenario Kafka --no-rerank
  python benchmark/run_benchmark.py ragas --limit 5
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import socket
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


BENCH_DIR = ROOT / "benchmark"
REPORT_DIR = BENCH_DIR / "reports"
RAGAS_QA = BENCH_DIR / "ragas_qa_50.jsonl"
RETRIEVAL_QA = BENCH_DIR / "retrieval_rk_50.jsonl"


def load_jsonl(
    path: Path,
    *,
    limit: int | None = None,
    scenario: str | None = None,
    ids: str | None = None,
) -> list[dict[str, Any]]:
    selected_ids = {item.strip() for item in (ids or "").split(",") if item.strip()}
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if scenario and row.get("scenario") != scenario:
                continue
            if selected_ids and row.get("id") not in selected_ids:
                continue
            rows.append(row)
            if limit and len(rows) >= limit:
                break
    return rows


def now_tag() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def write_report(name: str, payload: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / f"{name}_{now_tag()}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def preflight_milvus() -> None:
    from pymilvus import MilvusClient

    from app.config import settings

    uri = f"http://{settings.milvus_host}:{settings.milvus_port}"
    try:
        parsed = urlparse(uri)
        host = parsed.hostname or settings.milvus_host
        port = parsed.port or settings.milvus_port
        with socket.create_connection((host, port), timeout=2.0):
            pass
        client = MilvusClient(uri=uri)
        if not client.has_collection(settings.milvus_collection):
            raise RuntimeError(f"collection not found: {settings.milvus_collection}")
    except Exception as exc:
        raise SystemExit(
            "Milvus is not ready, benchmark would produce false misses.\n"
            f"  uri={uri}\n"
            f"  collection={settings.milvus_collection}\n"
            f"  error={type(exc).__name__}: {exc}\n\n"
            "Run:\n"
            "  docker compose up -d\n"
            "  python scripts/ingest_kb_corpus.py --reset --batch 8"
        ) from exc


def mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def short(text: str, n: int = 72) -> str:
    text = " ".join(str(text).split())
    return text[: n - 1] + "…" if len(text) > n else text


def is_relevant(hit: dict[str, Any], gold: dict[str, Any]) -> bool:
    source_ok = not gold.get("source") or hit.get("source") == gold.get("source")
    chapter_need = str(gold.get("chapter_contains") or "")
    chapter_ok = not chapter_need or chapter_need in str(hit.get("chapter") or "")
    return source_ok and chapter_ok


@dataclass
class RetrievalScore:
    hit: float
    mrr: float
    recall: float
    first_rank: int | None


def score_hits(
    hits: list[dict[str, Any]],
    relevant: list[dict[str, Any]],
    k: int,
    relevant_groups: list[list[dict[str, Any]]] | None = None,
) -> RetrievalScore:
    """按知识点组计算检索指标。

    - 同一 group 内是替代来源 (OR): 命中任意文档即可。
    - 不同 group 是独立知识点 (AND): recall 统计覆盖了多少组。
    - 旧题库只有 relevant 时，整组 relevant 默认视为同一知识点的替代来源。
    """
    top = hits[:k]
    groups = relevant_groups or ([relevant] if relevant else [])
    matched_groups: set[int] = set()
    first_rank: int | None = None
    for rank, hit in enumerate(top, 1):
        for gi, alternatives in enumerate(groups):
            if gi in matched_groups:
                continue
            if any(is_relevant(hit, gold) for gold in alternatives):
                matched_groups.add(gi)
                if first_rank is None:
                    first_rank = rank
    hit = 1.0 if first_rank is not None else 0.0
    mrr = 1.0 / first_rank if first_rank else 0.0
    recall = len(matched_groups) / len(groups) if groups else 0.0
    return RetrievalScore(hit=hit, mrr=mrr, recall=recall, first_rank=first_rank)


async def run_retrieval(args: argparse.Namespace) -> dict[str, Any]:
    from app.config import settings
    from app.rag.retrieval import build_context

    preflight_milvus()
    rows = load_jsonl(RETRIEVAL_QA, limit=args.limit, scenario=args.scenario, ids=args.ids)
    if not rows:
        raise SystemExit("No retrieval benchmark rows selected.")

    original_hybrid = settings.rag_hybrid_enabled
    original_rerank = settings.rag_rerank_enabled
    original_retrieve_k = settings.rag_retrieve_k
    original_bm25_weight = settings.rag_hybrid_bm25_weight
    original_rrf_k = settings.rag_hybrid_rrf_k
    original_parent_rerank = settings.rag_rerank_use_parent_context
    settings.rag_hybrid_enabled = original_hybrid and not args.no_hybrid
    settings.rag_rerank_enabled = original_rerank and not args.no_rerank
    if args.retrieve_k is not None:
        settings.rag_retrieve_k = args.retrieve_k
    if args.bm25_weight is not None:
        settings.rag_hybrid_bm25_weight = args.bm25_weight
    if args.rrf_k is not None:
        settings.rag_hybrid_rrf_k = args.rrf_k
    if args.no_parent_rerank:
        settings.rag_rerank_use_parent_context = False

    hits_scores: list[float] = []
    mrr_scores: list[float] = []
    recall_scores: list[float] = []
    details: list[dict[str, Any]] = []

    print(
        f"retrieval benchmark | rows={len(rows)} | k={args.k} | "
        f"hybrid={settings.rag_hybrid_enabled} | rerank={settings.rag_rerank_enabled} | "
        f"retrieve_k={settings.rag_retrieve_k} | "
        f"bm25_weight={settings.rag_hybrid_bm25_weight} | "
        f"rrf_k={settings.rag_hybrid_rrf_k} | "
        f"parent_rerank={settings.rag_rerank_use_parent_context}"
    )
    print("-" * 96)

    t0 = time.perf_counter()
    for i, row in enumerate(rows, 1):
        q = str(row["query"])
        _context, _hit_count, _sources, meta = await build_context(q, top_k=args.k)
        score = score_hits(
            meta,
            row.get("relevant") or [],
            args.k,
            relevant_groups=row.get("relevant_groups"),
        )
        hits_scores.append(score.hit)
        mrr_scores.append(score.mrr)
        recall_scores.append(score.recall)

        status = "OK" if score.hit else "MISS"
        top_desc = " | ".join(
            f"{h.get('source')}::{h.get('chapter')}:{h.get('score')}" for h in meta[: min(args.k, 3)]
        )
        print(
            f"[{i:02d}/{len(rows):02d}] {status:<4} "
            f"hit@{args.k}={mean(hits_scores):.3f} "
            f"mrr@{args.k}={mean(mrr_scores):.3f} "
            f"recall@{args.k}={mean(recall_scores):.3f} | {row['scenario']} | {short(q)}"
        )
        if args.verbose:
            print(f"    top: {top_desc}")

        details.append(
            {
                "id": row.get("id"),
                "scenario": row.get("scenario"),
                "query": q,
                "score": score.__dict__,
                "hits": meta,
                "relevant": row.get("relevant") or [],
                "relevant_groups": row.get("relevant_groups"),
            }
        )

    elapsed = time.perf_counter() - t0
    summary = {
        "mode": "retrieval",
        "k": args.k,
        "rows": len(rows),
        "hybrid": settings.rag_hybrid_enabled,
        "rerank": settings.rag_rerank_enabled,
        "retrieve_k": settings.rag_retrieve_k,
        "bm25_weight": settings.rag_hybrid_bm25_weight,
        "rrf_k": settings.rag_hybrid_rrf_k,
        "parent_rerank": settings.rag_rerank_use_parent_context,
        "hit_at_k": mean(hits_scores),
        "mrr_at_k": mean(mrr_scores),
        "recall_at_k": mean(recall_scores),
        "elapsed_sec": elapsed,
        "details": details,
    }
    out = write_report("retrieval", summary)
    print("-" * 96)
    print(
        f"final | hit@{args.k}={summary['hit_at_k']:.3f} "
        f"mrr@{args.k}={summary['mrr_at_k']:.3f} "
        f"recall@{args.k}={summary['recall_at_k']:.3f} "
        f"elapsed={elapsed:.1f}s"
    )
    print(f"report: {out}")
    settings.rag_hybrid_enabled = original_hybrid
    settings.rag_rerank_enabled = original_rerank
    settings.rag_retrieve_k = original_retrieve_k
    settings.rag_hybrid_bm25_weight = original_bm25_weight
    settings.rag_hybrid_rrf_k = original_rrf_k
    settings.rag_rerank_use_parent_context = original_parent_rerank
    return summary


async def retrieve_context(question: str) -> tuple[str, list[str], list[dict[str, Any]]]:
    from app.rag.retrieval import build_context

    context_text, hits, _sources, meta = await build_context(question)
    if hits == 0:
        return context_text, [], meta
    chunks = [c.strip() for c in context_text.split("\n\n## 来源 ") if c.strip()]
    chunks = [c if c.startswith("## 来源 ") else f"## 来源 {c}" for c in chunks]
    return context_text, chunks or [context_text], meta


async def generate_answer(question: str, context_text: str) -> str:
    from app.core.llm import get_chat_llm

    llm = get_chat_llm(temperature=0.0, timeout=60.0, max_tokens=700)
    prompt = f"""[知识库上下文]
{context_text}

[问题]
{question}

[回答要求]
1. 只使用知识库上下文中明确出现的信息，不调用常识补全。
2. 不得新增上下文没有出现的命令、参数名、默认值、阈值、异常类、因果关系或操作顺序。
3. 忽略与问题无关的来源；不同来源冲突时不自行裁决。
4. 第一段直接回答问题，并复用问题中的核心术语；不要只罗列孤立短语。
5. 回答前先找出与问题核心术语或同义表达匹配的句子；只要上下文能支持一个有效要点，就必须回答该要点。
6. 仅当所有来源都与问题无关、无法支持任何有效判断或动作时，才说明“知识库未提供相关信息”。
7. 不输出来源编号、引用标签、背景介绍、泛化建议或重复总结。
8. 控制在 2-5 个要点；每个要点包含“判断或动作 + 必要理由”。

[回答]"""
    resp = await llm.ainvoke(
        [
            (
                "system",
                "你是证据约束严格的 SRE 知识库助手。"
                "你的任务是抽取和组织证据，不是凭经验扩写。"
                "回答中的每个事实性陈述都必须能由给定上下文直接推出；"
                "无法直接支持的内容必须省略。",
            ),
            ("human", prompt),
        ]
    )
    return str(getattr(resp, "content", "") or "").strip()


def make_ragas_judge_and_embeddings():
    from openai import OpenAI
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import llm_factory

    from app.config import settings
    from app.core.embedding import get_embeddings

    model = settings.dashscope_chat_model
    if model.lower().startswith("deepseek"):
        client = OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
    else:
        client = OpenAI(api_key=settings.dashscope_api_key, base_url=settings.dashscope_base_url)

    kwargs: dict[str, Any] = {"temperature": 0.0, "max_tokens": 4096, "timeout": 60.0}
    if model.lower().startswith("deepseek"):
        kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
    return llm_factory(model, client=client, **kwargs), LangchainEmbeddingsWrapper(get_embeddings())


def run_single_ragas(sample: dict[str, Any], judge: Any, embeddings: Any) -> dict[str, float]:
    from ragas import evaluate
    from ragas.dataset_schema import EvaluationDataset
    from ragas.metrics import AnswerRelevancy, ContextPrecision, ContextRecall, Faithfulness

    dataset = EvaluationDataset.from_list([sample])
    result = evaluate(
        dataset=dataset,
        metrics=[
            Faithfulness(llm=judge),
            AnswerRelevancy(llm=judge, embeddings=embeddings),
            ContextPrecision(llm=judge),
            ContextRecall(llm=judge),
        ],
        llm=judge,
        embeddings=embeddings,
        show_progress=False,
    )
    row = result.to_pandas().iloc[0].to_dict()
    scores: dict[str, float] = {}
    for key in ("faithfulness", "answer_relevancy", "context_precision", "context_recall"):
        val = row.get(key)
        try:
            num = float(val)
            scores[key] = 0.0 if math.isnan(num) else num
        except Exception:
            scores[key] = 0.0
    return scores


def make_openevals_evaluators() -> tuple[Any, str, str]:
    """加载 OpenEvals 官方 rubric，复用项目 Chat LLM.

    DeepSeek 兼容接口当前不支持 response_format=json_schema，因此不直接使用
    create_async_llm_as_judge 的结构化输出路径，而是保留官方 prompt 后自行解析 JSON。
    """
    from openevals.prompts import RAG_GROUNDEDNESS_PROMPT, RAG_HELPFULNESS_PROMPT

    from app.core.llm import get_chat_llm

    judge = get_chat_llm(temperature=0.0, timeout=60.0, max_retries=1)
    return judge, RAG_GROUNDEDNESS_PROMPT, RAG_HELPFULNESS_PROMPT


def _parse_openeval_response(content: str) -> tuple[float, str]:
    """解析 judge 的 JSON；允许模型包裹 markdown code fence."""
    text = content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text[:-3]
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError(f"judge 未返回 JSON: {content[:200]}")
    data = json.loads(text[start : end + 1])
    score = max(0.0, min(1.0, float(data["score"])))
    return score, str(data.get("reasoning") or "")


async def _run_openeval_prompt(judge: Any, prompt: str) -> tuple[float, str]:
    output_instruction = """

Return JSON only, without markdown:
{"score": 0.0, "reasoning": "brief explanation"}
The score must be a number from 0.0 to 1.0.
"""
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = await judge.ainvoke(
                [
                    (
                        "system",
                        "You are an impartial evaluator. Follow the rubric exactly and return valid JSON only.",
                    ),
                    ("human", prompt + output_instruction),
                ]
            )
            return _parse_openeval_response(str(getattr(response, "content", "") or ""))
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                await asyncio.sleep(1.5 * (attempt + 1))
    assert last_error is not None
    raise last_error


async def run_openevals(
    *,
    question: str,
    answer: str,
    contexts: list[str],
    evaluators: tuple[Any, str, str],
) -> dict[str, Any]:
    """并行计算 OpenEvals groundedness/helpfulness，失败时不阻断 RAGAS."""
    judge, groundedness_prompt, helpfulness_prompt = evaluators
    context_text = "\n\n".join(contexts) if contexts else "(无召回)"
    requests = (
        _run_openeval_prompt(
            judge,
            groundedness_prompt.format(
                context=context_text,
                outputs=json.dumps({"answer": answer}, ensure_ascii=False),
            ),
        ),
        _run_openeval_prompt(
            judge,
            helpfulness_prompt.format(
                inputs=json.dumps({"question": question}, ensure_ascii=False),
                outputs=json.dumps({"answer": answer}, ensure_ascii=False),
            ),
        ),
    )
    grounded_result, helpful_result = await asyncio.gather(*requests, return_exceptions=True)

    def unpack(result: Any) -> tuple[float | None, str]:
        if isinstance(result, BaseException):
            return None, f"{type(result).__name__}: {result}"
        return result

    return {
        "groundedness": unpack(grounded_result)[0],
        "helpfulness": unpack(helpful_result)[0],
        "groundedness_reason": unpack(grounded_result)[1],
        "helpfulness_reason": unpack(helpful_result)[1],
        "error": isinstance(grounded_result, BaseException)
        or isinstance(helpful_result, BaseException),
    }


async def run_ragas(args: argparse.Namespace) -> dict[str, Any]:
    from app.config import settings

    preflight_milvus()
    rows = load_jsonl(RAGAS_QA, limit=args.limit, scenario=args.scenario, ids=args.ids)
    if not rows:
        raise SystemExit("No RAGAS benchmark rows selected.")

    if args.retrieve_k is not None:
        settings.rag_retrieve_k = args.retrieve_k
    if args.bm25_weight is not None:
        settings.rag_hybrid_bm25_weight = args.bm25_weight
    if args.rrf_k is not None:
        settings.rag_hybrid_rrf_k = args.rrf_k

    judge, embeddings = make_ragas_judge_and_embeddings()
    metric_names = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    rolling: dict[str, list[float]] = {m: [] for m in metric_names}
    openevals_enabled = not args.no_openevals
    openevals_evaluators = make_openevals_evaluators() if openevals_enabled else None
    openevals_rolling: dict[str, list[float]] = {
        "groundedness": [],
        "helpfulness": [],
    }
    details: list[dict[str, Any]] = []

    print(
        f"ragas benchmark | rows={len(rows)} | openevals={openevals_enabled} | "
        f"retrieve_k={settings.rag_retrieve_k} | "
        f"bm25_weight={settings.rag_hybrid_bm25_weight} | "
        f"rrf_k={settings.rag_hybrid_rrf_k}"
    )
    print("-" * 96)

    t0 = time.perf_counter()
    for i, row in enumerate(rows, 1):
        q = str(row["question"])
        context_text, contexts, hits_meta = await retrieve_context(q)
        answer = await generate_answer(q, context_text)
        sample = {
            "user_input": q,
            "retrieved_contexts": contexts or ["(无召回)"],
            "response": answer,
            "reference": str(row["ground_truth"]),
        }
        scores = run_single_ragas(sample, judge, embeddings)
        for m in metric_names:
            rolling[m].append(scores[m])
        openeval_scores: dict[str, Any] | None = None
        if openevals_evaluators is not None:
            openeval_scores = await run_openevals(
                question=q,
                answer=answer,
                contexts=contexts,
                evaluators=openevals_evaluators,
            )
            for metric in ("groundedness", "helpfulness"):
                value = openeval_scores[metric]
                if value is not None:
                    openevals_rolling[metric].append(float(value))

        line = (
            f"[{i:02d}/{len(rows):02d}] "
            f"faith={mean(rolling['faithfulness']):.3f} "
            f"rel={mean(rolling['answer_relevancy']):.3f} "
            f"cprec={mean(rolling['context_precision']):.3f} "
            f"crecall={mean(rolling['context_recall']):.3f}"
        )
        if openevals_enabled:
            ground_avg = mean(openevals_rolling["groundedness"])
            help_avg = mean(openevals_rolling["helpfulness"])
            line += (
                f" ground={ground_avg:.3f}"
                f" help={help_avg:.3f}"
            )
        line += f" | {row['scenario']} | {short(q)}"
        print(line)
        if args.verbose:
            print(f"    score={scores}")
            if openeval_scores is not None:
                print(
                    "    openevals="
                    f"ground={openeval_scores['groundedness']} "
                    f"help={openeval_scores['helpfulness']}"
                )
                print(f"    ground_reason={short(openeval_scores['groundedness_reason'], 220)}")
                print(f"    help_reason={short(openeval_scores['helpfulness_reason'], 220)}")
            print(f"    answer={short(answer, 180)}")

        details.append(
            {
                "id": row.get("id"),
                "scenario": row.get("scenario"),
                "question": q,
                "ground_truth": row.get("ground_truth"),
                "answer": answer,
                "contexts": contexts,
                "hits": hits_meta,
                "scores": scores,
                "openevals": openeval_scores,
            }
        )

    elapsed = time.perf_counter() - t0
    summary = {
        "mode": "ragas",
        "rows": len(rows),
        "retrieve_k": settings.rag_retrieve_k,
        "bm25_weight": settings.rag_hybrid_bm25_weight,
        "rrf_k": settings.rag_hybrid_rrf_k,
        "elapsed_sec": elapsed,
        "averages": {m: mean(v) for m, v in rolling.items()},
        "openevals_enabled": openevals_enabled,
        "openevals_averages": (
            {m: mean(v) for m, v in openevals_rolling.items()}
            if openevals_enabled
            else {}
        ),
        "details": details,
    }
    out = write_report("ragas", summary)
    print("-" * 96)
    avg = summary["averages"]
    final_line = (
        f"final | faith={avg['faithfulness']:.3f} "
        f"rel={avg['answer_relevancy']:.3f} "
        f"cprec={avg['context_precision']:.3f} "
        f"crecall={avg['context_recall']:.3f}"
    )
    if openevals_enabled:
        oe_avg = summary["openevals_averages"]
        final_line += (
            f" ground={oe_avg['groundedness']:.3f}"
            f" help={oe_avg['helpfulness']:.3f}"
        )
    final_line += f" elapsed={elapsed:.1f}s"
    print(final_line)
    print(f"report: {out}")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Realtime benchmark runner")
    sub = parser.add_subparsers(dest="mode", required=True)

    ret = sub.add_parser("retrieval", help="Run retrieval R@K benchmark")
    ret.add_argument("--k", type=int, default=3, help="Top-k for hit/mrr/recall")
    ret.add_argument("--limit", type=int, default=None)
    ret.add_argument("--scenario", type=str, default=None)
    ret.add_argument("--ids", type=str, default=None, help="Comma-separated benchmark IDs")
    ret.add_argument("--no-hybrid", action="store_true")
    ret.add_argument("--no-rerank", action="store_true")
    ret.add_argument("--retrieve-k", type=int, default=None, help="Override RAG_RETRIEVE_K")
    ret.add_argument("--bm25-weight", type=float, default=None, help="Override RAG_HYBRID_BM25_WEIGHT")
    ret.add_argument("--rrf-k", type=int, default=None, help="Override RAG_HYBRID_RRF_K")
    ret.add_argument(
        "--no-parent-rerank",
        action="store_true",
        help="Rerank with child chunk only instead of parent context",
    )
    ret.add_argument("--verbose", action="store_true")

    rag = sub.add_parser("ragas", help="Run RAGAS benchmark")
    rag.add_argument("--limit", type=int, default=None)
    rag.add_argument("--scenario", type=str, default=None)
    rag.add_argument("--ids", type=str, default=None, help="Comma-separated benchmark IDs")
    rag.add_argument("--retrieve-k", type=int, default=None, help="Override RAG_RETRIEVE_K")
    rag.add_argument("--bm25-weight", type=float, default=None, help="Override RAG_HYBRID_BM25_WEIGHT")
    rag.add_argument("--rrf-k", type=int, default=None, help="Override RAG_HYBRID_RRF_K")
    rag.add_argument(
        "--no-openevals",
        action="store_true",
        help="Disable OpenEvals groundedness/helpfulness judges",
    )
    rag.add_argument("--verbose", action="store_true")
    return parser


async def amain() -> None:
    args = build_parser().parse_args()
    if args.mode == "retrieval":
        await run_retrieval(args)
    elif args.mode == "ragas":
        await run_ragas(args)
    else:
        raise SystemExit(f"unknown mode: {args.mode}")


def main() -> None:
    asyncio.run(amain())


if __name__ == "__main__":
    main()
