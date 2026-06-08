# Tempo metrics generator processor updates failing

> Group: **Observability**  
> Service: **Grafana Tempo**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `15m`

## 现象 / Description

Tempo metrics generator processor updates are failing for {{ $labels.job }} ({{ $value }} failures in 5m).

## PromQL 查询

```promql
sum by (job) (increase(tempo_metrics_generator_active_processors_update_failed_total[5m])) > 2
```

## 故障定位

- 触发该告警时, 检查 Grafana Tempo 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Tempo
