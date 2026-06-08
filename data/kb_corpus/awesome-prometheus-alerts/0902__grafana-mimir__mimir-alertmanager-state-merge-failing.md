# Mimir alertmanager state merge failing

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `10m`

## 现象 / Description

Mimir alertmanager {{ $labels.job }} is failing to merge state updates ({{ $value | humanize }}/s).

## PromQL 查询

```promql
rate(cortex_alertmanager_partial_state_merges_failed_total[5m]) > 0.05
```

## 处理建议 / Comments

Threshold of 0.05/s avoids firing on transient single-event spikes.

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
