"""一次性 RAG 评测脚本: 用 Ragas 量化项目 RAG 路径的质量。

跑什么:
  对 data/eval/qa.jsonl 里每条 {question, ground_truth},
  ① 走项目真实的 RAG 检索 (app.rag.retrieval.build_context, 走 Milvus 混合检索 + rerank);
  ② 用项目真实的 LLM (app.core.llm.get_chat_llm) 基于检索上下文生成回答;
  ③ 把 (question, retrieved_contexts, answer, ground_truth) 喂给 Ragas 4 个指标:
       Faithfulness        答案是否忠于检索到的上下文 (有没有编)
       AnswerRelevancy     答案是否切题
       ContextPrecision    检索结果是否相关 (排得准不准)
       ContextRecall       检索是否覆盖了 ground_truth (漏了多少)
  ④ 输出 markdown 报告到 data/eval/report.md。

运行依赖 (真栈, 不是沙箱):
  - Postgres 起 (其实评测路径不碰 PG, 但 import 链需要 settings 可加载, 你已有 .env)
  - Milvus 起 + 已 ingest_kb_corpus 入库
  - DASHSCOPE_API_KEY 配好 (或 DEEPSEEK_API_KEY / 本地 ollama)

用法:
  python scripts/eval_ragas.py                          # 全部跑
  python scripts/eval_ragas.py --limit 3                # 只跑 3 条
  python scripts/eval_ragas.py --qa data/eval/qa.jsonl  # 自定义题集
  python scripts/eval_ragas.py --out data/eval/r.md     # 自定义输出
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

# 让脚本能从仓库根目录 import 到 app.*
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# ============================================================
# 1) 准备数据: 读 qa.jsonl + 走真实 RAG 检索 + LLM 生成答案
# ============================================================

def read_qa(path: Path, limit: int | None = None) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
            if limit and len(items) >= limit:
                break
    return items


async def retrieve(question: str) -> tuple[str, list[str]]:
    """走项目真实的 RAG: 混合检索 + rerank, 返回 (context_text, chunks_list)。"""
    from app.rag.retrieval import build_context

    context_text, hits, _sources, hits_meta = await build_context(question)
    if hits == 0:
        return context_text, []
    # Ragas 要看到和生成答案相同的信息量。hits_meta.preview 只有 240 字展示片段,
    # 用它评 faithfulness 会误判答案"不在上下文中"; 这里按来源块拆完整 context_text。
    chunks = [c.strip() for c in context_text.split("\n\n## 来源 ") if c.strip()]
    chunks = [c if c.startswith("## 来源 ") else f"## 来源 {c}" for c in chunks]
    if not chunks:
        chunks = [context_text]
    return context_text, chunks


_ANSWER_SYS = (
    "你是 SRE 助手。只根据给定的 [上下文] 回答问题。"
    "若上下文不足,如实说不知道。回答简洁,3-5 句话内。"
)


async def generate_answer(question: str, context_text: str) -> str:
    """用项目自己的 LLM 工厂生成回答 (按 .env 中的 model 配置: DashScope/DeepSeek/Ollama)。"""
    from app.core.llm import get_chat_llm

    llm = get_chat_llm(temperature=0.0, timeout=60.0)
    prompt = f"[上下文]\n{context_text}\n\n[问题] {question}\n\n[回答]"
    resp = await llm.ainvoke([("system", _ANSWER_SYS), ("human", prompt)])
    return str(getattr(resp, "content", "") or "").strip()


async def build_samples(items: list[dict[str, str]]) -> list[dict[str, Any]]:
    """给每条 QA 真跑一次"检索+生成", 拼成 Ragas SingleTurnSample 的 dict 形态。"""
    out: list[dict[str, Any]] = []
    for i, qa in enumerate(items, 1):
        q = str(qa.get("question") or "").strip()
        gt = str(qa.get("ground_truth") or "").strip()
        if not q:
            continue
        print(f"  [{i}/{len(items)}] {q[:50]}...")
        try:
            ctx_text, chunks = await retrieve(q)
            ans = await generate_answer(q, ctx_text)
        except Exception as exc:
            print(f"    ⚠ 跳过: {type(exc).__name__}: {exc}")
            continue
        out.append({
            "user_input": q,
            "retrieved_contexts": chunks or ["(无召回)"],
            "response": ans,
            "reference": gt,
        })
    return out


# ============================================================
# 2) 跑 Ragas 评测
# ============================================================

def run_ragas(samples: list[dict[str, Any]]):
    """喂给 Ragas, 用项目同一份 LLM 当裁判, 返回 EvaluationResult。"""
    from ragas import evaluate
    from ragas.dataset_schema import EvaluationDataset
    from ragas.metrics import (
        AnswerRelevancy,
        ContextPrecision,
        ContextRecall,
        Faithfulness,
    )

    # Ragas 0.4+ 的 collections metrics 只接受 Ragas 原生 InstructorLLM。
    # 仍复用项目 .env 中的 OpenAI-compatible 模型配置。
    from openai import OpenAI
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import llm_factory

    from app.config import settings
    from app.core.embedding import get_embeddings

    judge_model = settings.dashscope_chat_model
    if judge_model.lower().startswith("deepseek"):
        judge_client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
        )
    else:
        judge_client = OpenAI(
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url,
        )
    judge_kwargs: dict[str, Any] = {
        "temperature": 0.0,
        "max_tokens": 4096,
        "timeout": 60.0,
    }
    if judge_model.lower().startswith("deepseek"):
        judge_kwargs["extra_body"] = {"thinking": {"type": "disabled"}}

    ragas_judge = llm_factory(
        judge_model,
        client=judge_client,
        **judge_kwargs,
    )

    ragas_embedding = LangchainEmbeddingsWrapper(get_embeddings())

    dataset = EvaluationDataset.from_list(samples)
    result = evaluate(
        dataset=dataset,
        metrics=[
            Faithfulness(llm=ragas_judge),
            AnswerRelevancy(llm=ragas_judge, embeddings=ragas_embedding),
            ContextPrecision(llm=ragas_judge),
            ContextRecall(llm=ragas_judge),
        ],
        llm=ragas_judge,
        embeddings=ragas_embedding,
        show_progress=True,
    )
    return result


# ============================================================
# 3) 输出 markdown 报告
# ============================================================

def render_report(samples: list[dict[str, Any]], result, out: Path) -> None:
    """汇总 + 逐条得分, 写成 markdown。"""
    df = result.to_pandas()
    lines: list[str] = []
    lines.append("# Ragas RAG 评测报告\n")
    lines.append(f"样本数: **{len(samples)}**\n")

    # 汇总平均分
    metric_cols = [c for c in df.columns if c not in {
        "user_input", "retrieved_contexts", "response", "reference",
    }]
    lines.append("## 平均得分\n")
    lines.append("| 指标 | 平均分 | 含义 |")
    lines.append("|---|---|---|")
    explain = {
        "faithfulness": "答案是否忠于检索上下文 (无编造)",
        "answer_relevancy": "答案是否切题",
        "context_precision": "检索排序是否准 (相关在前)",
        "context_recall": "检索是否覆盖 ground_truth (无遗漏)",
    }
    for c in metric_cols:
        avg = df[c].mean()
        lines.append(f"| {c} | {avg:.3f} | {explain.get(c, '')} |")
    lines.append("")

    # 逐条结果
    lines.append("## 逐条结果\n")
    for i, row in df.iterrows():
        lines.append(f"### Q{i+1}: {row['user_input']}\n")
        lines.append(f"- **ground_truth**: {row.get('reference', '')}")
        lines.append(f"- **生成回答**: {row['response']}")
        scores = " | ".join(f"{c}={row[c]:.3f}" if isinstance(row[c], float) else f"{c}={row[c]}" for c in metric_cols)
        lines.append(f"- **得分**: {scores}")
        lines.append("")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n✅ 报告已写: {out}")


# ============================================================
# 入口
# ============================================================

async def amain(args) -> None:
    qa_path = Path(args.qa)
    out_path = Path(args.out)
    items = read_qa(qa_path, limit=args.limit)
    print(f"读到 {len(items)} 条 QA, 开始检索+生成...")
    samples = await build_samples(items)
    print(f"\n准备好 {len(samples)} 个样本, 跑 Ragas...")
    result = run_ragas(samples)
    render_report(samples, result, out_path)


def main() -> None:
    p = argparse.ArgumentParser(description="一次性 RAG 评测 (Ragas)")
    p.add_argument("--qa", type=str, default="data/eval/qa.jsonl", help="QA 题集 jsonl")
    p.add_argument("--out", type=str, default="data/eval/report.md", help="报告输出路径")
    p.add_argument("--limit", type=int, default=None, help="只跑前 N 条")
    args = p.parse_args()
    asyncio.run(amain(args))


if __name__ == "__main__":
    main()
