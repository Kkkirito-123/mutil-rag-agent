# Loki process too many restarts

> Group: **Observability**  
> Service: **Loki**  
> Exporter: `embedded-exporter`  
> Severity: **warning**

## 现象 / Description

A loki process had too many restarts (target {{ $labels.instance }})

## PromQL 查询

```promql
changes(process_start_time_seconds{job=~".*loki.*"}[15m]) > 2
```

## 故障定位

- 触发该告警时, 检查 Loki 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Loki
