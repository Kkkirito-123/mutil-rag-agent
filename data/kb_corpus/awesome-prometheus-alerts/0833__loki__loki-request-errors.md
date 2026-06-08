# Loki request errors

> Group: **Observability**  
> Service: **Loki**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `15m`

## 现象 / Description

The {{ $labels.job }} and {{ $labels.route }} are experiencing {{ printf "%.2f" $value }}% errors.

## PromQL 查询

```promql
100 * sum(rate(loki_request_duration_seconds_count{status_code=~"5.."}[1m])) by (namespace, job, route) / sum(rate(loki_request_duration_seconds_count[1m])) by (namespace, job, route) > 10 and sum(rate(loki_request_duration_seconds_count[1m])) by (namespace, job, route) > 0
```

## 故障定位

- 触发该告警时, 检查 Loki 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Loki
