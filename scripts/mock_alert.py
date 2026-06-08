"""\u544a\u8b66\u6a21\u62df\u5668 \u2014 \u6a21\u62df Prometheus Alertmanager \u53d1 webhook \u7ed9 multi_agent.

\u7528\u6cd5:
    # \u968f\u673a\u53d1\u4e00\u6761\u544a\u8b66, \u9a8c\u8bc1\u81ea\u52a8\u94fe\u8def
    python scripts/mock_alert.py

    # \u6307\u5b9a\u573a\u666f
    python scripts/mock_alert.py --scenario redis
    python scripts/mock_alert.py --scenario disk
    python scripts/mock_alert.py --scenario cpu

    # \u6301\u7eed\u6a21\u62df: \u6bcf 30s \u968f\u673a\u53d1\u4e00\u6761 (\u6a21\u62df\u4e00\u4e2a\u52a0\u73ed\u591c)
    python scripts/mock_alert.py --watch --interval 30

    # \u67e5\u770b\u540e\u53f0\u8dd1\u8fc7\u4ec0\u4e48
    python scripts/mock_alert.py --list-history

    # \u6e05\u7a7a\u5386\u53f2 (\u6f14\u793a\u91cd\u542f\u7528)
    python scripts/mock_alert.py --clear-history

\u5de5\u4f5c\u539f\u7406:
    1. \u672c\u811a\u672c POST \u4e00\u4efd Alertmanager v4 webhook \u6807\u51c6 JSON
    2. multi_agent /api/v1/webhook/alertmanager \u63a5\u6536\u540e\u540e\u53f0\u542f\u52a8 AIOps \u8bca\u65ad
    3. \u8bca\u65ad\u8fc7\u7a0b\u5168\u81ea\u52a8 (Plan-Execute-Replan), \u7ed3\u679c\u5199\u5165 data/alert_history.jsonl
    4. \u53ef\u7528 --list-history \u6216\u8bbf\u95ee /api/v1/webhook/history \u67e5\u770b
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
import uuid
from datetime import datetime, timezone

import requests

# Windows UTF-8 stdout
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


SCENARIOS = {
    "redis": {
        "alertname": "RedisMemoryHigh",
        "severity": "critical",
        "service": "redis",
        "instance": "redis-master-01:6379",
        "summary": "Redis \u5b9e\u4f8b\u5185\u5b58\u4f7f\u7528\u7387 98%",
        "description": (
            "redis_memory_used_bytes / redis_memory_max_bytes = 0.982, "
            "\u6301\u7eed 12 \u5206\u949f\u3002\u5ba2\u6237\u7aef\u8fde\u63a5\u88ab\u5f3a\u5236\u65ad\u5f00, "
            "\u4e0a\u6e38\u670d\u52a1 user-service \u51fa\u73b0 Connection refused\u3002"
        ),
        "runbook_url": "https://example.com/runbooks/redis-memory-high",
    },
    "disk": {
        "alertname": "DiskSpaceLow",
        "severity": "critical",
        "service": "node",
        "instance": "k8s-node-03:9100",
        "summary": "\u8282\u70b9\u78c1\u76d8\u7a7a\u95f4\u4e0d\u8db3 5%",
        "description": (
            "node_filesystem_avail_bytes{mountpoint=\"/\"} \u4ec5\u4f59 4.2GB (3.8%), "
            "\u6301\u7eed 8 \u5206\u949f\u3002\u5f71\u54cd: kubelet \u53ef\u80fd\u8fdb\u5165 disk-pressure, "
            "Pod \u88ab\u9a71\u9010\u3002"
        ),
        "runbook_url": "https://example.com/runbooks/disk-full",
    },
    "cpu": {
        "alertname": "CPUHighUsage",
        "severity": "warning",
        "service": "app-server",
        "instance": "app-server-07:9100",
        "summary": "\u670d\u52a1\u5668 CPU \u4f7f\u7528\u7387\u6301\u7eed 92%",
        "description": (
            "rate(node_cpu_seconds_total{mode!=\"idle\"}[5m]) = 0.92, "
            "\u6301\u7eed 7 \u5206\u949f\u3002\u63a5\u53e3\u54cd\u5e94 P99 \u5ef6\u8fdf\u4ece 80ms \u4e0a\u6da8\u5230 1.2s\u3002"
        ),
        "runbook_url": "https://example.com/runbooks/cpu-high",
    },
    "memory": {
        "alertname": "ProcessMemoryLeak",
        "severity": "warning",
        "service": "payment-service",
        "instance": "payment-svc-pod-x9f3:8080",
        "summary": "payment-service Pod \u5185\u5b58\u6cc4\u6f0f\u8ff9\u8c61",
        "description": (
            "process_resident_memory_bytes \u5728 6 \u5c0f\u65f6\u5185\u4ece 800MB \u589e\u957f\u5230 3.2GB, "
            "GC \u540e\u4e0d\u91ca\u653e\u3002Pod limit=4GB, \u9884\u8ba1 90 \u5206\u949f\u540e OOMKilled\u3002"
        ),
    },
    "kafka": {
        "alertname": "KafkaISRShrinking",
        "severity": "warning",
        "service": "kafka",
        "instance": "kafka-broker-02:9092",
        "summary": "Kafka ISR \u5217\u8868\u9891\u7e41\u62d6\u52a8",
        "description": (
            "topic=user-events, partition=3, ISR \u8fc7\u53bb 10 \u5206\u949f\u53d1\u751f 7 \u6b21 shrink, "
            "\u526f\u672c\u540c\u6b65\u5ef6\u8fdf > 30s\u3002"
        ),
    },
}


def build_payload(scenario_key: str) -> dict:
    """\u6784\u9020 Alertmanager v4 webhook payload."""
    sc = SCENARIOS[scenario_key]
    now = datetime.now(timezone.utc).isoformat()
    return {
        "version": "4",
        "groupKey": f"{{}}:{{alertname='{sc['alertname']}'}}",
        "truncatedAlerts": 0,
        "status": "firing",
        "receiver": "multi-agent-aiops",
        "groupLabels": {"alertname": sc["alertname"]},
        "commonLabels": {
            "alertname": sc["alertname"],
            "severity": sc["severity"],
            "service": sc.get("service", ""),
        },
        "commonAnnotations": {},
        "externalURL": "http://prometheus.example.com:9090",
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": sc["alertname"],
                    "severity": sc["severity"],
                    "service": sc.get("service", ""),
                    "instance": sc["instance"],
                },
                "annotations": {
                    "summary": sc["summary"],
                    "description": sc["description"],
                    **(
                        {"runbook_url": sc["runbook_url"]}
                        if "runbook_url" in sc
                        else {}
                    ),
                },
                "startsAt": now,
                "endsAt": "0001-01-01T00:00:00Z",
                "generatorURL": (
                    "http://prometheus.example.com:9090/graph?g0.expr="
                    + sc["alertname"]
                ),
                "fingerprint": uuid.uuid4().hex[:16],
            }
        ],
    }


def fire_alert(base_url: str, scenario_key: str) -> None:
    payload = build_payload(scenario_key)
    sc = SCENARIOS[scenario_key]
    url = f"{base_url}/api/v1/webhook/alertmanager"

    print("=" * 70)
    print(f"\u23f0 [{datetime.now():%H:%M:%S}] \u53d1\u9001\u544a\u8b66")
    print(f"  alertname : {sc['alertname']}")
    print(f"  severity  : {sc['severity']}")
    print(f"  instance  : {sc['instance']}")
    print(f"  summary   : {sc['summary']}")
    print(f"  -> POST {url}")
    print("-" * 70)

    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            data = r.json()
            accepted = data.get("accepted", [])
            print(f"\u2713 webhook \u8fd4\u56de 200, \u5165\u961f {len(accepted)} \u6761\u8bca\u65ad\u4efb\u52a1")
            for item in accepted:
                print(f"  \u00b7 incident_group_id = {item.get('incident_group_id', '')}")
                print(f"    task_id           = {item.get('task_id', '')}")
                print(f"    enqueued          = {item.get('enqueued', False)}")
            print("\n\ud83d\udcdd \u8bca\u65ad\u4efb\u52a1\u5df2\u5165 Redis Stream, \u9700\u8981\u542f\u52a8 Worker \u6d88\u8d39:")
            print("   python -m app.workers.diagnosis_worker")
            print("\n\ud83d\udd0d \u67e5\u770b\u8bca\u65ad\u7ed3\u679c:")
            print("   python scripts/mock_alert.py --list-history")
            print(f"   \u6216 \u6d4f\u89c8\u5668\u8bbf\u95ee {base_url}/api/v1/webhook/history")
        else:
            print(f"\u2717 webhook \u8fd4\u56de {r.status_code}")
            print(f"  body: {r.text[:500]}")
    except requests.RequestException as e:
        print(f"\u2717 \u8bf7\u6c42\u5931\u8d25: {e}")
        print(f"  \u8bf7\u786e\u8ba4 multi_agent \u5728\u8fd0\u884c: {base_url}")


def list_history(base_url: str, limit: int = 10) -> None:
    url = f"{base_url}/api/v1/webhook/history?limit={limit}"
    try:
        r = requests.get(url, timeout=10)
    except requests.RequestException as e:
        print(f"\u2717 \u8bf7\u6c42\u5931\u8d25: {e}")
        return

    if r.status_code != 200:
        print(f"\u2717 HTTP {r.status_code}: {r.text[:200]}")
        return

    data = r.json()
    items = data.get("items", [])
    if not items:
        print("\u53bb\u54ea\u4e86? \u8fd8\u6ca1\u540e\u53f0\u8bca\u65ad\u8bb0\u5f55\u3002\u5148\u8dd1: python scripts/mock_alert.py")
        return

    print("=" * 70)
    print(f"\ud83d\udcd6 \u6700\u8fd1 {len(items)} \u6761\u540e\u53f0\u8bca\u65ad\u8bb0\u5f55 (\u65b0 \u2192 \u65e7)")
    print("=" * 70)
    for i, rec in enumerate(items, 1):
        payload = rec.get("payload", {}) or {}
        print(f"\n[{i}] {rec.get('created_at', '?')[:19]} -> {rec.get('finished_at') or '(running/pending)'}")
        print(f"    task_id       : {rec.get('id', '?')}")
        print(f"    status        : {rec.get('status', '?')}")
        print(f"    incident_group: {rec.get('incident_group_id', '?')}")
        print(f"    alertname     : {payload.get('alertname', '?')}")
        print(f"    severity      : {payload.get('severity', '?')}")
        print(f"    instance      : {payload.get('instance', '?')}")
        print(f"    mode          : {rec.get('diagnosis_mode', '?')}")
        print(f"    attempts      : {rec.get('attempts', 0)}")
        if rec.get("error"):
            print(f"    \u2717 error      : {rec['error']}")
        report = payload.get("report", "") or ""
        if report:
            preview = report[:300].replace("\n", " ")
            print(f"    report        : {preview}{'...' if len(report) > 300 else ''}")
            print(f"    report_chars  : {len(report)}")
        else:
            print(f"    report        : (\u672a\u751f\u6210)")
    print()


def clear_history(base_url: str) -> None:
    url = f"{base_url}/api/v1/webhook/history"
    try:
        r = requests.delete(url, timeout=10)
        if r.status_code == 200:
            print("\u2713 \u5df2\u6e05\u7a7a\u5386\u53f2")
        else:
            print(f"\u2717 HTTP {r.status_code}: {r.text}")
    except requests.RequestException as e:
        print(f"\u2717 \u8bf7\u6c42\u5931\u8d25: {e}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="\u6a21\u62df Alertmanager \u53d1 webhook \u7ed9 multi_agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "\u53ef\u7528\u573a\u666f: " + ", ".join(SCENARIOS.keys()) + "\n\n"
            "\u6f14\u793a\u6d41\u7a0b:\n"
            "  1. \u542f multi_agent (cd ../multi_agent && .\\run.ps1)\n"
            "  2. \u8dd1 python scripts/mock_alert.py  (\u6a21\u62df\u544a\u8b66)\n"
            "  3. \u7b49 30-90s\n"
            "  4. \u8dd1 python scripts/mock_alert.py --list-history  (\u770b\u7ed3\u679c)"
        ),
    )
    ap.add_argument(
        "--url",
        default="http://localhost:9900",
        help="multi_agent base URL (\u9ed8\u8ba4 http://localhost:9900)",
    )
    ap.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()),
        default=None,
        help="\u6307\u5b9a\u544a\u8b66\u573a\u666f (\u4e0d\u4f20\u5c31\u968f\u673a\u9009)",
    )
    ap.add_argument(
        "--watch",
        action="store_true",
        help="\u6301\u7eed\u6a21\u5f0f, \u6bcf interval \u79d2\u53d1\u4e00\u6761 (\u9ed8\u8ba4\u4e00\u6b21\u6027)",
    )
    ap.add_argument(
        "--interval",
        type=int,
        default=60,
        help="--watch \u6a21\u5f0f\u4e0b\u7684\u95f4\u9694\u79d2\u6570 (\u9ed8\u8ba4 60)",
    )
    ap.add_argument(
        "--list-history",
        action="store_true",
        help="\u67e5\u770b\u540e\u53f0\u8bca\u65ad\u5386\u53f2",
    )
    ap.add_argument(
        "--clear-history",
        action="store_true",
        help="\u6e05\u7a7a\u5386\u53f2 (\u6f14\u793a\u91cd\u542f\u7528)",
    )
    args = ap.parse_args()

    if args.list_history:
        list_history(args.url)
        return
    if args.clear_history:
        clear_history(args.url)
        return

    base = args.url.rstrip("/")

    if args.watch:
        print(f"\ud83d\udd04 watch \u6a21\u5f0f: \u6bcf {args.interval}s \u968f\u673a\u53d1\u4e00\u6761\u544a\u8b66 (Ctrl+C \u9000\u51fa)")
        try:
            while True:
                key = args.scenario or random.choice(list(SCENARIOS.keys()))
                fire_alert(base, key)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n\u9000\u51fa watch \u6a21\u5f0f")
    else:
        key = args.scenario or random.choice(list(SCENARIOS.keys()))
        fire_alert(base, key)


if __name__ == "__main__":
    main()
