# Mimir ingester TSDB checkpoint creation failed

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `15m`

## 现象 / Description

Mimir ingester {{ $labels.instance }} is failing to create TSDB checkpoints ({{ $value | humanize }}/s).

## PromQL 查询

```promql
rate(cortex_ingester_tsdb_checkpoint_creations_failed_total[5m]) > 0.05
```

## 处理建议 / Comments

Threshold of 0.05/s avoids firing on transient single-event spikes.

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
