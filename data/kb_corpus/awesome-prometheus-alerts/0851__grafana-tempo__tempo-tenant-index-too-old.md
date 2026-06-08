# Tempo tenant index too old

> Group: **Observability**  
> Service: **Grafana Tempo**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Tenant index for {{ $labels.tenant }} is {{ $value }}s old.

## PromQL 查询

```promql
max by (tenant) (tempodb_blocklist_tenant_index_age_seconds) > 600
```

## 处理建议 / Comments

Threshold of 600s (10 minutes). Adjust based on your tenant index build interval.

## 故障定位

- 触发该告警时, 检查 Grafana Tempo 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Tempo
