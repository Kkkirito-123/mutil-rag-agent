# Mimir alertmanager instance has no tenants

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `1h`

## 现象 / Description

Mimir alertmanager {{ $labels.instance }} has no tenants assigned.

## PromQL 查询

```promql
(cortex_alertmanager_tenants_owned == 0) and on (instance) (cortex_alertmanager_tenants_owned offset 1h > 0)
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
