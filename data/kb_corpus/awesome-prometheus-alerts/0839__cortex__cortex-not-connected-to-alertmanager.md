# Cortex not connected to Alertmanager

> Group: **Observability**  
> Service: **Cortex**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Cortex not connected to Alertmanager (instance {{ $labels.instance }})

## PromQL 查询

```promql
cortex_prometheus_notifications_alertmanagers_discovered < 1
```

## 故障定位

- 触发该告警时, 检查 Cortex 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Cortex
