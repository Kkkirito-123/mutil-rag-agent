# Mimir store gateway has not synced bucket

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Mimir store-gateway {{ $labels.instance }} has not synced the bucket for more than 30 minutes.

## PromQL 查询

```promql
(time() - cortex_bucket_stores_blocks_last_successful_sync_timestamp_seconds{component="store-gateway"} > 1800) and cortex_bucket_stores_blocks_last_successful_sync_timestamp_seconds{component="store-gateway"} > 0
```

## 处理建议 / Comments

Threshold of 30 minutes. Adjust based on your sync interval.

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
