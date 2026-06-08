# Loki request latency

> Group: **Observability**  
> Service: **Loki**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

The {{ $labels.job }} {{ $labels.route }} is experiencing {{ printf "%.2f" $value }}s 99th percentile latency.

## PromQL 查询

```promql
histogram_quantile(0.99, sum(rate(loki_request_duration_seconds_bucket{route!~"(?i).*tail.*"}[5m])) by (namespace, job, route, le)) > 1
```

## 故障定位

- 触发该告警时, 检查 Loki 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Loki
