# Tempo metrics generator service graphs dropping spans

> Group: **Observability**  
> Service: **Grafana Tempo**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

Tempo metrics generator is dropping {{ printf "%.2f" $value }}% of spans in service graphs for {{ $labels.job }}.

## PromQL 查询

```promql
100 * sum by (job) (rate(tempo_metrics_generator_processor_service_graphs_dropped_spans_total[5m])) / sum by (job) (rate(tempo_metrics_generator_spans_received_total[5m])) > 0.5 and sum by (job) (rate(tempo_metrics_generator_spans_received_total[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Grafana Tempo 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Grafana Tempo
