# Tempo distributor usage tracker errors

> Group: **Observability**  
> Service: **Grafana Tempo**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `30m`

## 现象 / Description

Tempo distributor usage tracker errors for {{ $labels.job }} at {{ $value | humanize }}/s (reason {{ $labels.reason }}).

## PromQL 查询

```promql
sum by (job, reason) (rate(tempo_distributor_usage_tracker_errors_total[5m])) > 0.05
```

## 处理建议 / Comments

Threshold of 0.05/s avoids firing on transient single-event spikes.

## 故障定位

- 触发该告警时, 检查 Grafana Tempo 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Tempo
