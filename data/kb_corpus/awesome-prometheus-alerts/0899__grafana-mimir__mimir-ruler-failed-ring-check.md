# Mimir ruler failed ring check

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Mimir ruler {{ $labels.job }} is failing ring checks ({{ $value | humanize }}/s).

## PromQL 查询

```promql
sum by (job) (rate(cortex_ruler_ring_check_errors_total[5m])) > 0.05
```

## 处理建议 / Comments

Threshold of 0.05/s avoids firing on transient single-event spikes.

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
