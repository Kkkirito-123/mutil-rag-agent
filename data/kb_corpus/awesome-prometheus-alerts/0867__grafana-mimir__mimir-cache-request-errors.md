# Mimir cache request errors

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Mimir cache {{ $labels.name }} is experiencing {{ printf "%.2f" $value }}% errors for {{ $labels.operation }} operation.

## PromQL 查询

```promql
(sum by (name, operation, job) (rate(thanos_cache_operation_failures_total[5m])) / sum by (name, operation, job) (rate(thanos_cache_operations_total[5m]))) * 100 > 5 and sum by (name, operation, job) (rate(thanos_cache_operations_total[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
