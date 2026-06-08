#!/usr/bin/env bash
# 一键本地拉起高并发架构 (改造文档第 10 步), 适合 macOS/Linux 演示:
#   1) docker compose 起基础设施 (redis / postgres / milvus / open-websearch)
#   2) 后台起 1 个多-worker uvicorn API
#   3) 后台起 N 个诊断 Worker (worker-1..N), 共享 Redis 全局并发槽 + 优先级队列
#
# 用法:
#   scripts/run_all.sh                # 默认 3 个 worker
#   WORKERS=5 UVICORN_WORKERS=4 scripts/run_all.sh
#   PYTHON=/path/to/conda/python scripts/run_all.sh
#   SKIP_INFRA=1 scripts/run_all.sh   # 基础设施已在跑, 只起 API+Worker
#   SKIP_MCP=1 scripts/run_all.sh     # 跳过本机 MCP 工具服务
#
# 进程 PID 写入 .run/, 日志写入 logs/; 停止用 scripts/stop_all.sh
set -euo pipefail

PYTHON="${PYTHON:-python}"
WORKERS="${WORKERS:-3}"
UVICORN_WORKERS="${UVICORN_WORKERS:-4}"
APP_PORT="${APP_PORT:-9900}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p logs .run

# 1) 基础设施 (仅基础设施, 不带 app profile)
if [[ "${SKIP_INFRA:-0}" != "1" ]]; then
  echo "[run_all] 启动基础设施 (docker compose up -d)..."
  docker compose up -d redis postgres etcd minio standalone open-websearch
  echo "[run_all] 等待 Redis / Postgres 就绪..."
  for _ in $(seq 1 30); do
    if docker compose exec -T redis redis-cli ping >/dev/null 2>&1; then break; fi
    sleep 1
  done
fi

# 2) MCP 工具服务。必须在 API 之前启动, 因为 API lifespan 只在启动时加载 MCP 工具。
if [[ "${SKIP_MCP:-0}" != "1" ]]; then
  echo "[run_all] 启动 MCP 工具服务..."
  PYTHON="$PYTHON" bash scripts/run_mcp.sh
  echo "[run_all] 等待 MCP 端口就绪..."
  for port in 8005 8006 8008 8009 8011; do
    for _ in $(seq 1 20); do
      if nc -z 127.0.0.1 "$port" >/dev/null 2>&1; then break; fi
      sleep 0.5
    done
  done
fi

# 3) API (多 uvicorn worker)
echo "[run_all] 启动 API (uvicorn workers=$UVICORN_WORKERS, port=$APP_PORT)..."
UVICORN_WORKERS="$UVICORN_WORKERS" APP_PORT="$APP_PORT" PYTHON="$PYTHON" \
  nohup bash scripts/run_api.sh > logs/api.log 2>&1 &
echo $! > .run/api.pid
echo "[run_all]   API pid=$(cat .run/api.pid) -> logs/api.log"

# 4) N 个 Worker
for i in $(seq 1 "$WORKERS"); do
  name="worker-$i"
  PYTHON="$PYTHON" nohup bash scripts/run_worker.sh "$name" > "logs/$name.log" 2>&1 &
  echo $! > ".run/$name.pid"
  echo "[run_all]   $name pid=$(cat ".run/$name.pid") -> logs/$name.log"
done

echo ""
echo "[run_all] 全部启动完成。"
echo "  API:        http://localhost:$APP_PORT  (前端同端口)"
echo "  MCP:        http://localhost:8005/8006/8008/8009/8011/mcp"
echo "  队列/槽位:   curl http://localhost:$APP_PORT/api/v1/queue/status"
echo "  看日志:      tail -f logs/api.log logs/worker-1.log"
echo "  压测:        $PYTHON scripts/loadtest.py submit --n 100 --concurrency 20"
echo "  停止:        scripts/stop_all.sh"
