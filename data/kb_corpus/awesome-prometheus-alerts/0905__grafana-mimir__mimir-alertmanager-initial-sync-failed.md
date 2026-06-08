# Mimir alertmanager initial sync failed

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **warning**

## 现象 / Description

Mimir alertmanager {{ $labels.job }} failed initial state sync.

## PromQL 查询

```promql
increase(cortex_alertmanager_state_initial_sync_completed_total{outcome="failed"}[1m]) > 0
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
