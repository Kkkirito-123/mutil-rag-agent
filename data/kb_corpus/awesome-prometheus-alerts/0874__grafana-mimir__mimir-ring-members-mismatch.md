# Mimir ring members mismatch

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

Mimir {{ $labels.name }} ring has inconsistent member counts across instances.

## PromQL 查询

```promql
max by (name, job) (sum by (name, job, instance) (cortex_ring_members)) != min by (name, job) (sum by (name, job, instance) (cortex_ring_members))
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
