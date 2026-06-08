#!/usr/bin/env bash
# 停止 scripts/run_all.sh 起的 API + Worker 进程 (改造文档第 10 步)。
# 默认不动 docker 基础设施; 带 --infra 连基础设施一起停。
#   scripts/stop_all.sh
#   scripts/stop_all.sh --infra
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -d .run ]]; then
  for pidfile in .run/*.pid; do
    [[ -e "$pidfile" ]] || continue
    pid="$(cat "$pidfile" 2>/dev/null || true)"
    name="$(basename "$pidfile" .pid)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      echo "[stop_all] 停止 $name (pid=$pid)"
      # 先 TERM 整个进程组 (uvicorn 会派生子 worker), 失败再 kill 单进程
      kill -TERM "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
    fi
    rm -f "$pidfile"
  done
fi

# 兜底: 清掉可能残留的 uvicorn / worker 进程
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "app.diagnosis_worker" 2>/dev/null || true
pkill -f "mcp_servers/.*_server.py" 2>/dev/null || true

if [[ "${1:-}" == "--infra" ]]; then
  echo "[stop_all] 停止 docker 基础设施 (docker compose down)..."
  docker compose down
fi

echo "[stop_all] 完成。"
