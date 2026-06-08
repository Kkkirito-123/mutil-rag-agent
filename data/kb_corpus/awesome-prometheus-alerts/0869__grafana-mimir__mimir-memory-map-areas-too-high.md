# Mimir memory map areas too high

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Mimir {{ $labels.job }} is using {{ printf "%.0f" $value }}% of its memory map area limit.

## PromQL 查询

```promql
process_memory_map_areas{job=~".*(ingester|cortex|mimir|store-gateway).*"} / process_memory_map_areas_limit{job=~".*(ingester|cortex|mimir|store-gateway).*"} * 100 > 80 and process_memory_map_areas_limit{job=~".*(ingester|cortex|mimir|store-gateway).*"} > 0
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
