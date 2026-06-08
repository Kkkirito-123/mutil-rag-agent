# Jaeger query service slow responses

> Group: **Observability**  
> Service: **Jaeger**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Jaeger query service on {{ $labels.instance }} p99 response latency is {{ $value | humanizeDuration }}.

## PromQL 查询

```promql
histogram_quantile(0.99, sum(rate(http_server_request_duration_seconds_bucket{http_route="/api/traces"}[5m])) by (le, instance, job, namespace)) > 2
```

## 处理建议 / Comments

Threshold of 2s is a rough default. Adjust based on your storage backend and data volume.

## 故障定位

- 触发该告警时, 检查 Jaeger 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Jaeger
