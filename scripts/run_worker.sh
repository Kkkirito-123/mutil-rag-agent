#!/usr/bin/env bash
# 启动单个诊断 Worker (改造文档第 3/10 步)。
# 用法: scripts/run_worker.sh worker-1
#   PYTHON=/path/to/python scripts/run_worker.sh worker-2   # 指定解释器 (如 conda 环境)
set -euo pipefail

NAME="${1:-worker-1}"
PYTHON="${PYTHON:-python}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[run_worker] starting $NAME (python=$PYTHON)"
exec "$PYTHON" -m app.diagnosis_worker --name "$NAME"
