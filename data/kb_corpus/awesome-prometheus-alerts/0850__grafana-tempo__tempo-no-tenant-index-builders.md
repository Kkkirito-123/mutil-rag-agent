# Tempo no tenant index builders

> Group: **Observability**  
> Service: **Grafana Tempo**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

No tenant index builders for tenant {{ $labels.tenant }}. Tenant index will quickly become stale.

## PromQL 查询

```promql
sum by (tenant) (tempodb_blocklist_tenant_index_builder) == 0 and on() max(tempodb_blocklist_length) > 0
```

## 故障定位

- 触发该告警时, 检查 Grafana Tempo 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Tempo
