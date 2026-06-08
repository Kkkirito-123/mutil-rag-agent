# Mimir ingester unhealthy

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `15m`

## 现象 / Description

Mimir has {{ $value }} unhealthy ingester(s) in the ring.

## PromQL 查询

```promql
min by (job) (cortex_ring_members{state="Unhealthy", name="ingester"}) > 0
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
