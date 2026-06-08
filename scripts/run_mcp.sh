#!/usr/bin/env bash
# Start local MCP tool servers used by the AIOps agent.
# Usage:
#   scripts/run_mcp.sh
#   PYTHON=/path/to/python scripts/run_mcp.sh
set -euo pipefail

PYTHON="${PYTHON:-python}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p logs .run

servers=(
  "system:mcp_servers/system_server.py:8005"
  "websearch:mcp_servers/websearch_server.py:8006"
  "winlog:mcp_servers/winlog_server.py:8008"
  "network:mcp_servers/network_server.py:8009"
  "docker:mcp_servers/docker_server.py:8011"
)

for spec in "${servers[@]}"; do
  IFS=":" read -r name script port <<< "$spec"
  pidfile=".run/mcp-$name.pid"
  if [[ -f "$pidfile" ]]; then
    pid="$(cat "$pidfile" 2>/dev/null || true)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      echo "[run_mcp] $name already running pid=$pid"
      continue
    fi
  fi
  echo "[run_mcp] starting $name on port $port ($script)"
  PYTHON="$PYTHON" nohup "$PYTHON" "$script" > "logs/mcp-$name.log" 2>&1 &
  echo $! > "$pidfile"
done

echo "[run_mcp] MCP servers started. Logs: logs/mcp-*.log"
