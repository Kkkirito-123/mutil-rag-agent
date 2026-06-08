# Thanos Store Series Gate Latency High

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-store`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

Thanos Store {{$labels.job}} has a 99th percentile latency of {{$value}} seconds for store series gate requests.

## PromQL 查询

```promql
(histogram_quantile(0.99, sum by (job, le) (rate(thanos_bucket_store_series_gate_duration_seconds_bucket[5m]))) > 2 and sum by (job) (rate(thanos_bucket_store_series_gate_duration_seconds_count[5m])) > 0)
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Thanos
