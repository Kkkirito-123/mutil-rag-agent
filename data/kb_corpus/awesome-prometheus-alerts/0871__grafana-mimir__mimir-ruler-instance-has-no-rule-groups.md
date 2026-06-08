# Mimir ruler instance has no rule groups

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `1h`

## 现象 / Description

Mimir ruler {{ $labels.instance }} has no rule groups assigned.

## PromQL 查询

```promql
(cortex_ruler_managers_total == 0) and on (instance) (cortex_ruler_managers_total offset 1h > 0)
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
