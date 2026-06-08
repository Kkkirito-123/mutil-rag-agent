# 并发与队列测试指令

适用于当前 `MultiAgentAIOps` 项目。默认地址：

```bash
BASE_URL=http://localhost:9900
cd /path/to/MultiAgentAIOps
```

> 注意：`submit` 和 `webhook` 会创建真实诊断任务，Worker 会调用 LLM，可能产生费用。  
> 第一次建议使用 `n=6` 或 `n=10`，确认链路正常后再逐步加压。

## 1. 当前并发配置

```bash
grep -E \
  'MANUAL_DIAGNOSIS_CONCURRENCY|WORKER_DIAGNOSIS_CONCURRENCY|AGENT_MAX_CONCURRENCY|EXECUTOR_MAX_PARALLEL|RATE_LIMIT' \
  .env
```

当前主要限制：

```text
MANUAL_DIAGNOSIS_CONCURRENCY=2   同步 SSE 诊断全局最多 2 个
WORKER_DIAGNOSIS_CONCURRENCY=2   所有后台 Worker 合计最多真正执行 2 个诊断任务
AGENT_MAX_CONCURRENCY=2          Agent 内部并发限制
EXECUTOR_MAX_PARALLEL=6          单轮最多并行执行 6 个安全工具
```

接口限流默认值（未写入 `.env` 时使用）：

```text
RATE_LIMIT_MANUAL_PER_IP_PER_MIN=20
RATE_LIMIT_WEBHOOK_PER_SOURCE_PER_MIN=500
RATE_LIMIT_WEBHOOK_PER_IP_PER_SEC=50
```

## 2. 启动与健康检查

```bash
docker compose --profile app up -d --build
```

检查容器：

```bash
docker compose ps
```

检查 API、Milvus、Postgres、Redis、MCP：

```bash
curl -sS "$BASE_URL/api/v1/health/ready" | python -m json.tool
```

通过标准：

- HTTP 返回 `200`
- `status` 为 `ready`
- Milvus、Postgres、Redis 状态均为 `ok`
- MCP 显示 `tools_count: 15`

## 3. 实时观察窗口

压测时建议另外打开两个终端。

终端 A：每两秒观察队列、Worker 和并发槽：

```bash
while true; do
  clear
  date
  curl -sS "$BASE_URL/api/v1/queue/status" | python -m json.tool
  sleep 2
done
```

终端 B：观察 API 和 Worker 日志：

```bash
docker compose logs -f --tail=100 api worker-1 worker-2 worker-3
```

可选：观察容器资源：

```bash
docker stats \
  multi-agent-api \
  multi-agent-worker-1 \
  multi-agent-worker-2 \
  multi-agent-worker-3 \
  multi-agent-redis \
  multi-agent-postgres
```

重点字段：

```text
depth                  尚未被 Worker 领取的任务
pending                已领取但尚未 ACK 的任务
lag                    Consumer Group 尚未消费的消息
alive_workers          活跃 Worker 数
slots.worker_diagnosis 后台诊断槽占用，默认不能超过 2/2
slots.manual_diagnosis 同步诊断槽占用，默认不能超过 2/2
dlq_depth              最终失败后进入死信队列的数量
```

`stream_length` 是累计写入量，不会在任务完成后归零，不能用它判断队列是否排空。

## 4. 低成本冒烟测试

先确认脚本和提交链路可用：

```bash
python scripts/loadtest.py status
python scripts/loadtest.py submit --n 6 --concurrency 3
```

预期：

- 请求大部分返回 `2xx`
- 提交接口延迟明显低于完整诊断耗时
- `depth` 短暂上升后下降
- `slots.worker_diagnosis.used` 最大为 `2`
- 三个 Worker 都存活，但所有 Worker 合计只运行两个诊断

等待任务排空：

```bash
while true; do
  JSON="$(curl -sS "$BASE_URL/api/v1/queue/status")"
  echo "$JSON" | python -m json.tool
  echo "$JSON" | python -c '
import json, sys
d = json.load(sys.stdin)
done = d.get("depth", 0) == 0 and d.get("pending", 0) == 0 and d.get("lag", 0) == 0
raise SystemExit(0 if done else 1)
' && break
  sleep 5
done
```

## 5. 队列并发上限测试

```bash
python scripts/loadtest.py submit --n 20 --concurrency 20
```

当前单 IP 每分钟限制为 20，因此应在新的限流窗口执行。

预期：

- API 快速接收任务
- 队列出现堆积
- `slots.worker_diagnosis.used` 始终不超过 `2`
- Worker 完成任务后队列逐步回落
- API 不应崩溃或长时间无响应

同时查看任务状态统计：

```bash
docker compose exec -T postgres psql \
  -U multi_agent -d multi_agent_aiops \
  -c "SELECT status, count(*) FROM diagnosis_tasks GROUP BY status ORDER BY status;"
```

## 6. 手动接口限流测试

等待一分钟窗口重置后执行：

```bash
python scripts/loadtest.py submit --n 40 --concurrency 40
```

预期：

- 前 20 个左右返回 `2xx`
- 超出部分返回 `429`
- API 保持健康

限流测试的 `429` 是预期结果，不算系统失败。

## 7. Webhook 并发与去重测试

轻量测试：

```bash
python scripts/loadtest.py webhook --n 20 --concurrency 20
```

较高压力：

```bash
python scripts/loadtest.py webhook --n 100 --concurrency 100
```

混合严重等级，观察优先级队列：

```bash
python scripts/loadtest.py webhook --n 100 --concurrency 50 --severity mix
```

说明：

- 脚本会复用 50 组 `groupKey/fingerprint`，用于验证并发去重
- 相同活跃事件组只允许有一个 `pending/running` 任务
- 单 IP 默认每秒最多 50 个 Webhook，超过时出现 `429` 属于预期
- `critical` 应进入高优先级 Stream

检查是否出现同组多个活跃任务：

```bash
docker compose exec -T postgres psql \
  -U multi_agent -d multi_agent_aiops \
  -c "
SELECT incident_group_id, count(*)
FROM diagnosis_tasks
WHERE status IN ('pending', 'running')
GROUP BY incident_group_id
HAVING count(*) > 1;
"
```

通过标准：查询结果应为 `0 rows`。

## 8. 同步 SSE 全局并发测试

该测试会启动三个真实诊断。默认同步并发槽为 `2`，第三个请求应收到并发已满事件。

```bash
for i in 1 2 3; do
  curl -sN -X POST "$BASE_URL/api/v1/aiops/diagnose" \
    -H 'Content-Type: application/json' \
    -d "{
      \"session_id\":\"sse-concurrency-$i\",
      \"query\":\"检查当前主机 CPU、内存、磁盘和高占用进程\",
      \"diagnosis_mode\":\"fast\"
    }" > "/tmp/aiops-sse-$i.log" &
done
wait
```

检查输出：

```bash
for f in /tmp/aiops-sse-*.log; do
  echo "===== $f ====="
  rg 'concurrency_limited|并发|complete|error' "$f"
done
```

预期：

- 最多两个请求同时占用 `manual_diagnosis` 槽
- 第三个请求出现 `concurrency_limited` 或“并发已满”
- API 仍可访问健康检查

清理临时输出：

```bash
rm -f /tmp/aiops-sse-*.log
```

## 9. 工具内部并行测试

请求同时查询多个互不依赖的只读工具：

```bash
curl -sN -X POST "$BASE_URL/api/v1/aiops/diagnose" \
  -H 'Content-Type: application/json' \
  -d '{
    "session_id":"tool-parallel-test",
    "query":"同时查询当前 CPU、内存、磁盘、Top 进程和 Docker 容器状态，并汇总异常",
    "diagnosis_mode":"fast"
  }' | tee /tmp/tool-parallel-test.log
```

检查服务日志：

```bash
docker compose logs --since=10m api |
  rg 'ParallelAgent|parallel|batch|tool='
```

预期：

- 只读且 `concurrency_safe=true` 的工具可进入同一并行批次
- 单批并行数量不超过 `EXECUTOR_MAX_PARALLEL=6`
- `web_search`、写操作和未登记工具不应被盲目并行

## 10. Worker 横向扩展对比

注意：增加 Worker 数量不会突破全局槽上限。默认上限仍是：

```text
WORKER_DIAGNOSIS_CONCURRENCY=2
```

查看各 Worker：

```bash
curl -sS "$BASE_URL/api/v1/queue/status" |
  python -c '
import json, sys
d = json.load(sys.stdin)
for w in d.get("workers", []):
    print(w)
'
```

要测试吞吐随 Worker 数增加，需同时提高 `.env`：

```env
WORKER_DIAGNOSIS_CONCURRENCY=3
```

然后重建运行环境：

```bash
docker compose --profile app up -d --force-recreate \
  api worker-1 worker-2 worker-3
```

再次执行：

```bash
python scripts/loadtest.py submit --n 20 --concurrency 20
```

观察 `slots.worker_diagnosis.used` 是否可达到 `3/3`。测试后建议恢复为 `2`，避免超过模型配额。

## 11. 测试结果保存

```bash
mkdir -p benchmark/concurrency-results
STAMP="$(date +%Y%m%d-%H%M%S)"

python scripts/loadtest.py submit --n 20 --concurrency 20 \
  | tee "benchmark/concurrency-results/submit-$STAMP.log"

curl -sS "$BASE_URL/api/v1/queue/status" \
  | python -m json.tool \
  > "benchmark/concurrency-results/queue-$STAMP.json"

docker compose ps \
  > "benchmark/concurrency-results/containers-$STAMP.txt"
```

建议记录：

- 测试时间、机器配置
- API / Worker 数量
- 并发环境变量
- 总请求数和并发数
- 2xx、429、其它错误数
- P50、P95、P99
- 队列最高深度
- DLQ 数量
- 队列完全排空耗时

## 12. 测试数据清理

先等待队列完全排空，再清理历史。不要删除仍在 `pending/running` 的任务。

少量数据：进入“事件中心”，使用“全选可删除”与批量删除。

大量压测数据可在确认全部完成后执行以下测试专用清理：

```bash
docker compose exec -T postgres psql \
  -U multi_agent -d multi_agent_aiops <<'SQL'
BEGIN;

DELETE FROM approval_requests
WHERE task_id IN (
  SELECT dt.id
  FROM diagnosis_tasks dt
  JOIN incident_groups ig ON ig.id = dt.incident_group_id
  WHERE ig.metadata->>'source' LIKE 'submit:lt-%'
     OR ig.metadata->>'receiver' = 'loadtest'
);

DELETE FROM incident_groups
WHERE metadata->>'source' LIKE 'submit:lt-%'
   OR metadata->>'receiver' = 'loadtest';

DELETE FROM alerts a
WHERE (a.receiver LIKE 'submit:lt-%' OR a.receiver = 'loadtest')
  AND NOT EXISTS (
    SELECT 1 FROM incident_group_alerts iga WHERE iga.alert_id = a.id
  );

COMMIT;
SQL
```

该 SQL 只匹配 `scripts/loadtest.py` 使用的 `submit:lt-*` 和 `receiver=loadtest` 数据。

## 13. 最终通过标准

一次完整并发验证应满足：

- API 始终可通过 `/api/v1/health/ready`
- 队列提交接口无大量超时或连接错误
- 非限流场景主要为 `2xx`
- 限流场景按配置返回 `429`
- 同一事件组不存在多个活跃任务
- Worker 全局并发不突破配置上限
- 队列最终回落到 `depth=0`、`pending=0`、`lag=0`
- `dlq_depth` 没有异常增长
- 没有遗留永久占用的分布式并发槽
- API 与 Worker 没有持续增长的 CPU、内存或连接数
