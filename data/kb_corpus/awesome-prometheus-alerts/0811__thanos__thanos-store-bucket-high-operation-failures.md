# Thanos Store Bucket High Operation Failures

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-store`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

Thanos Store {{$labels.job}} Bucket is failing to execute {{$value | humanize}}% of operations.

## PromQL 查询

```promql
(sum by (job) (rate(thanos_objstore_bucket_operation_failures_total{job=~".*thanos-store.*"}[5m])) / sum by (job) (rate(thanos_objstore_bucket_operations_total{job=~".*thanos-store.*"}[5m])) * 100 > 5) and sum by (job) (rate(thanos_objstore_bucket_operations_total{job=~".*thanos-store.*"}[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Thanos
