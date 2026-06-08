# Mimir store gateway no synced tenants

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `1h`

## 现象 / Description

Mimir store-gateway {{ $labels.instance }} has no synced tenants.

## PromQL 查询

```promql
(min by (instance, job) (cortex_bucket_stores_tenants_synced{component="store-gateway"}) == 0) and on (instance) (cortex_bucket_stores_tenants_synced{component="store-gateway"} offset 1h > 0)
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
