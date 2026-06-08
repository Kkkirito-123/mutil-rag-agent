# Thanos Query Range Latency High

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-query`  
> Severity: **critical**  
> Duration (for): `10m`

## 现象 / Description

Thanos Query {{$labels.job}} has a 99th percentile latency of {{$value}} seconds for range queries.

## PromQL 查询

```promql
(histogram_quantile(0.99, sum by (job, le) (rate(http_request_duration_seconds_bucket{job=~".*thanos-query.*", handler="query_range"}[5m]))) > 90 and sum by (job) (rate(http_request_duration_seconds_count{job=~".*thanos-query.*", handler="query_range"}[5m])) > 0)
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Thanos
