"""高并发压测脚本 (改造文档第 11 步).

用 asyncio + httpx 对三个关键接口发压, 输出: 成功率 / P50·P95·P99 延迟 / 吞吐 / 429 限流命中,
并在压测前后打印一次 /queue/status 快照 (服务端可观测面: 队列深度、各优先级、并发槽、Worker)。

依赖: httpx (项目已装)。不依赖 hey/wrk/k6, 纯 Python 即可跑。

示例:
    # 场景一: 100 个手动诊断并发提交 (API 应快速返回 task_id, 任务进队列, 系统不崩)
    python scripts/loadtest.py submit --n 100 --concurrency 50

    # 混合优先级: 随机 severity, 验证 critical 插队
    python scripts/loadtest.py submit --n 100 --concurrency 50 --severity mix

    # 场景二: 500 条告警快速推送 (webhook 快速返回, 去重, 进 Redis)
    python scripts/loadtest.py webhook --n 500 --concurrency 100

    # 验证限流: 单 IP 狂刷, 看 429 命中比例
    python scripts/loadtest.py submit --n 200 --concurrency 100

    # 只看队列状态快照
    python scripts/loadtest.py status

    # 指定地址
    python scripts/loadtest.py submit --n 100 --base-url http://localhost:9900
"""

from __future__ import annotations

import argparse
import asyncio
import random
import time
from typing import Any

import httpx

SEVERITIES = ["critical", "high", "warning", "info"]
QUERIES = [
    "Redis 报 OOM command not allowed，怎么排查",
    "核心库 Postgres 连接数打满，5xx 暴涨",
    "磁盘使用率 95%，服务开始写失败",
    "某节点 CPU 持续 100%，请求变慢",
    "Kafka 消费延迟堆积，下游处理不过来",
    "Nginx 502 比例升高，怀疑上游超时",
]


def _percentile(sorted_vals: list[float], pct: float) -> float:
    if not sorted_vals:
        return 0.0
    k = max(0, min(len(sorted_vals) - 1, int(round((pct / 100.0) * (len(sorted_vals) - 1)))))
    return sorted_vals[k]


def _print_report(title: str, latencies_ms: list[float], codes: dict[int, int], elapsed_s: float, total: int) -> None:
    ok = sum(c for code, c in codes.items() if 200 <= code < 300)
    rate_limited = codes.get(429, 0)
    errors = total - ok - rate_limited
    s = sorted(latencies_ms)
    print("=" * 64)
    print(f"压测结果 · {title}")
    print("-" * 64)
    print(f"  总请求      : {total}")
    print(f"  成功(2xx)   : {ok}  ({ok / total * 100:.1f}%)" if total else "  成功(2xx)   : 0")
    print(f"  限流(429)   : {rate_limited}")
    print(f"  其它/失败   : {errors}")
    print(f"  状态码分布  : {dict(sorted(codes.items()))}")
    print(f"  总耗时      : {elapsed_s:.2f}s")
    print(f"  吞吐        : {total / elapsed_s:.1f} req/s" if elapsed_s > 0 else "  吞吐        : —")
    if s:
        print(f"  延迟 avg    : {sum(s) / len(s):.0f} ms")
        print(f"  延迟 P50    : {_percentile(s, 50):.0f} ms")
        print(f"  延迟 P95    : {_percentile(s, 95):.0f} ms")
        print(f"  延迟 P99    : {_percentile(s, 99):.0f} ms")
        print(f"  延迟 max    : {s[-1]:.0f} ms")
    print("=" * 64)


def _build_alert_payload(idx: int, severity: str) -> dict[str, Any]:
    alertname = random.choice(["RedisOOM", "PgConnSaturation", "DiskPressure", "HighCPU", "KafkaLag"])
    return {
        "version": "4",
        "groupKey": f"loadtest-{idx % 50}",  # 复用 groupKey 制造可去重场景
        "status": "firing",
        "receiver": "loadtest",
        "commonLabels": {"alertname": alertname, "severity": severity},
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": alertname,
                    "severity": severity,
                    "instance": f"node-{idx % 20}",
                    "service": random.choice(["redis", "postgres", "nginx", "kafka"]),
                },
                "annotations": {"summary": f"{alertname} firing on node-{idx % 20}"},
                "startsAt": "2026-06-08T00:00:00Z",
                "fingerprint": f"lt-{alertname}-{idx % 50}",  # 同 fingerprint 触发去重
            }
        ],
    }


async def _fetch_status(base_url: str) -> None:
    try:
        async with httpx.AsyncClient(timeout=10, trust_env=False) as cli:
            r = await cli.get(f"{base_url}/api/v1/queue/status")
            d = r.json()
        print(
            f"  [queue] depth={d.get('depth')} by_level={d.get('depth_by_level')} "
            f"pending={d.get('pending')} dlq={d.get('dlq_depth')} "
            f"slots={d.get('slots')} alive_workers={d.get('alive_workers')}"
        )
    except Exception as exc:
        print(f"  [queue] 取状态失败: {type(exc).__name__}: {exc}")


async def _run(args: argparse.Namespace, make_req) -> None:
    sem = asyncio.Semaphore(args.concurrency)
    latencies: list[float] = []
    codes: dict[int, int] = {}
    lock = asyncio.Lock()

    async with httpx.AsyncClient(timeout=args.timeout, trust_env=False) as cli:
        async def one(i: int) -> None:
            async with sem:
                t0 = time.perf_counter()
                try:
                    resp = await make_req(cli, i)
                    code = resp.status_code
                except Exception:
                    code = 0  # 连接错误/超时
                dt = (time.perf_counter() - t0) * 1000
                async with lock:
                    latencies.append(dt)
                    codes[code] = codes.get(code, 0) + 1

        print(f"[loadtest] 压测前队列快照:")
        await _fetch_status(args.base_url)
        print(f"[loadtest] 发压: n={args.n} concurrency={args.concurrency} ...")
        t0 = time.perf_counter()
        await asyncio.gather(*(one(i) for i in range(args.n)))
        elapsed = time.perf_counter() - t0

    _print_report(args.mode, latencies, codes, elapsed, args.n)
    print("[loadtest] 压测后队列快照 (观察 Worker 消费/队列回落):")
    await _fetch_status(args.base_url)


async def amain() -> None:
    p = argparse.ArgumentParser(description="高并发压测 (submit / webhook / status)")
    p.add_argument("mode", choices=["submit", "webhook", "status"], help="压测对象")
    p.add_argument("--base-url", default="http://localhost:9900")
    p.add_argument("--n", type=int, default=100, help="总请求数")
    p.add_argument("--concurrency", type=int, default=20, help="并发数")
    p.add_argument("--timeout", type=float, default=30.0)
    p.add_argument("--severity", default="warning", help="warning/critical/... 或 'mix' 随机")
    args = p.parse_args()

    base = args.base_url.rstrip("/")
    args.base_url = base

    if args.mode == "status":
        await _fetch_status(base)
        return

    if args.mode == "submit":
        async def make_req(cli: httpx.AsyncClient, i: int):
            sev = random.choice(SEVERITIES) if args.severity == "mix" else args.severity
            return await cli.post(
                f"{base}/api/v1/aiops/diagnose/submit",
                json={"query": random.choice(QUERIES), "severity": sev, "session_id": f"lt-{i}"},
            )
        await _run(args, make_req)

    elif args.mode == "webhook":
        async def make_req(cli: httpx.AsyncClient, i: int):
            sev = random.choice(SEVERITIES) if args.severity == "mix" else args.severity
            return await cli.post(
                f"{base}/api/v1/webhook/alertmanager",
                json=_build_alert_payload(i, sev),
            )
        await _run(args, make_req)


def main() -> None:
    asyncio.run(amain())


if __name__ == "__main__":
    main()
