# Cortex ingester unhealthy

> Group: **Observability**  
> Service: **Cortex**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Cortex has an unhealthy ingester

## PromQL 查询

```promql
cortex_ring_members{state="Unhealthy", name="ingester"} > 0
```

## 故障定位

- 触发该告警时, 检查 Cortex 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Cortex
