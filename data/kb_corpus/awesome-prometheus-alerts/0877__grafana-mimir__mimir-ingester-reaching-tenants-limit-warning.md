# Mimir ingester reaching tenants limit warning

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Mimir ingester {{ $labels.instance }} has reached {{ printf "%.0f" $value }}% of its tenants limit.

## PromQL 查询

```promql
(cortex_ingester_memory_users / ignoring(limit) cortex_ingester_instance_limits{limit="max_tenants"} * 100 > 70) and cortex_ingester_instance_limits{limit="max_tenants"} > 0
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
