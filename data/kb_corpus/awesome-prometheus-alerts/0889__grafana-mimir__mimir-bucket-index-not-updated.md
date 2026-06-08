# Mimir bucket index not updated

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Mimir bucket index for tenant {{ $labels.user }} has not been updated for more than 35 minutes.

## PromQL 查询

```promql
min by (user, job) (time() - cortex_bucket_index_last_successful_update_timestamp_seconds) > 2100
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
