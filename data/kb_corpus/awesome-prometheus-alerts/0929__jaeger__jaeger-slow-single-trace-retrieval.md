# Jaeger slow single trace retrieval

> Group: **Observability**  
> Service: **Jaeger**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Jaeger on {{ $labels.instance }} p99 latency for single trace retrieval is {{ $value | humanizeDuration }}.

## PromQL 查询

```promql
histogram_quantile(0.99, sum(rate(http_server_request_duration_seconds_bucket{http_route="/api/traces/{traceID}"}[5m])) by (le, instance, job, namespace)) > 5
```

## 处理建议 / Comments

Single trace retrieval (/api/traces/{traceID}) can be slower than search, especially for large traces.
Threshold of 5s is a rough default.

## 故障定位

- 触发该告警时, 检查 Jaeger 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Jaeger
