# Mimir compactor not cleaning up blocks

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `1h`

## 现象 / Description

Mimir compactor {{ $labels.instance }} has not cleaned up blocks in the last 6 hours.

## PromQL 查询

```promql
(time() - cortex_compactor_block_cleanup_last_successful_run_timestamp_seconds > 21600) and cortex_compactor_block_cleanup_last_successful_run_timestamp_seconds > 0
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
