# Benchmark

这个目录放两套评测集和一个实时评测脚本:

- `ragas_qa_50.jsonl`: 50 条端到端 RAGAS QA, 每个场景 5 条。
- `retrieval_rk_50.jsonl`: 50 条检索侧 R@K 题, 每个场景 5 条。
- `run_benchmark.py`: 支持 retrieval / ragas 两种模式, 逐题打印滚动指标。

## 前置条件

先确保 Docker 里的 Milvus 已启动, 并且已用当前 embedding 配置重建知识库:

```bash
docker compose up -d
python scripts/ingest_kb_corpus.py --reset --batch 8
```

## 检索侧 R@K

推荐先跑这个, 它最快, 能实时观察检索参数变化:

```bash
python benchmark/run_benchmark.py retrieval --k 3
```

常用参数:

```bash
# 看 R@5
python benchmark/run_benchmark.py retrieval --k 5

# 只跑某个场景
python benchmark/run_benchmark.py retrieval --scenario Kafka --k 3

# 关闭 rerank 做 A/B
python benchmark/run_benchmark.py retrieval --k 3 --no-rerank

# 关闭 hybrid 做 A/B
python benchmark/run_benchmark.py retrieval --k 3 --no-hybrid
```

输出指标:

- `hit@k`: top-k 中是否命中任意 gold。
- `mrr@k`: 第一个命中位置的倒数。
- `recall@k`: top-k 覆盖的知识点组比例。

Gold 规则:

- 旧格式 `relevant: [A, B, C]` 表示 A/B/C 是同一知识点的替代来源，命中任意一个即可。
- 多个独立知识点使用 `relevant_groups: [[A, B], [C, D]]`，组内是 OR，组间按覆盖率计算 recall。
- 这样 awesome 告警、自建 runbook、SOP 是替代答案时，不会因为未同时进入 top-k 而错误扣分。

## RAGAS 端到端

这个会调用 LLM 生成答案, 再用 RAGAS judge 打分, 会比较慢:

```bash
python benchmark/run_benchmark.py ragas --limit 5
```

默认同时运行 OpenEvals:

- `groundedness`: 回答是否由检索上下文支持。
- `helpfulness`: 回答是否真正解决用户问题。

如只想运行原来的 RAGAS 四项:

```bash
python benchmark/run_benchmark.py ragas --limit 5 --no-openevals
```

加 `--verbose` 会打印 OpenEvals 的扣分原因，并写入 JSON 报告。

全量 50 条:

```bash
python benchmark/run_benchmark.py ragas
```

结果会逐题打印滚动均值, 并写入:

- `benchmark/reports/retrieval_*.json`
- `benchmark/reports/ragas_*.json`
