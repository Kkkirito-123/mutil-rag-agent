# Mimir request errors

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `15m`

## 现象 / Description

Mimir {{ $labels.job }} {{ $labels.route }} is experiencing {{ printf "%.2f" $value }}% errors.

## PromQL 查询

```promql
100 * sum by (job, route) (rate(cortex_request_duration_seconds_count{status_code=~"5..", route!~"ready|debug_pprof"}[5m])) / sum by (job, route) (rate(cortex_request_duration_seconds_count{route!~"ready|debug_pprof"}[5m])) > 1 and sum by (job, route) (rate(cortex_request_duration_seconds_count{route!~"ready|debug_pprof"}[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
