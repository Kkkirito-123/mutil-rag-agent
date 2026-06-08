# Mimir KV store failure

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Mimir {{ $labels.job }} KV store {{ $labels.kv_name }} is failing with 100% error rate.

## PromQL 查询

```promql
(sum by (job, kv_name) (rate(cortex_kv_request_duration_seconds_count{status_code!~"2.."}[5m])) / sum by (job, kv_name) (rate(cortex_kv_request_duration_seconds_count[5m]))) == 1 and sum by (job, kv_name) (rate(cortex_kv_request_duration_seconds_count[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
