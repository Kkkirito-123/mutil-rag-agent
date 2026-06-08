# Mimir compactor not running compaction

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `15m`

## 现象 / Description

Mimir compactor {{ $labels.instance }} has not run compaction in the last 24 hours.

## PromQL 查询

```promql
(time() - cortex_compactor_last_successful_run_timestamp_seconds > 86400) and cortex_compactor_last_successful_run_timestamp_seconds > 0
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
