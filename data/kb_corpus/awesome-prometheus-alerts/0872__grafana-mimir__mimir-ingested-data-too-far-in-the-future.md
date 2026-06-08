# Mimir ingested data too far in the future

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Mimir ingester {{ $labels.job }} has ingested samples with timestamps more than 1 hour in the future.

## PromQL 查询

```promql
max by (job) (cortex_ingester_tsdb_head_max_timestamp_seconds - time() and cortex_ingester_tsdb_head_max_timestamp_seconds > 0) > 3600
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
