# Mimir compactor has consecutive failures

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Mimir compactor {{ $labels.instance }} has had {{ $value }} compaction failures in the last 2 hours.

## PromQL 查询

```promql
increase(cortex_compactor_runs_failed_total{reason!="shutdown"}[2h]) > 1
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
