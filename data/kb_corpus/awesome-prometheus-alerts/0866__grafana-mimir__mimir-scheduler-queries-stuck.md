# Mimir scheduler queries stuck

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `7m`

## 现象 / Description

There are {{ $value }} queued up queries in {{ $labels.job }}.

## PromQL 查询

```promql
sum by (job) (min_over_time(cortex_query_scheduler_queue_length[1m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
