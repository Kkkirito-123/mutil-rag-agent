# Promtail request errors

> Group: **Observability**  
> Service: **Promtail**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

The {{ $labels.job }} {{ $labels.route }} is experiencing {{ printf "%.2f" $value }}% errors.

## PromQL 查询

```promql
100 * sum(rate(promtail_request_duration_seconds_count{status_code=~"5..|failed"}[1m])) by (namespace, job, route, instance) / sum(rate(promtail_request_duration_seconds_count[1m])) by (namespace, job, route, instance) > 10 and sum(rate(promtail_request_duration_seconds_count[1m])) by (namespace, job, route, instance) > 0
```

## 故障定位

- 触发该告警时, 检查 Promtail 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Promtail
