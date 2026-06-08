# Mimir ingester TSDB WAL truncation failed

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **warning**

## 现象 / Description

Mimir ingester {{ $labels.instance }} is failing to truncate TSDB WAL ({{ $value | humanize }}/s).

## PromQL 查询

```promql
rate(cortex_ingester_tsdb_wal_truncations_failed_total[5m]) > 0.05
```

## 处理建议 / Comments

Threshold of 0.05/s avoids firing on transient single-event spikes.

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
