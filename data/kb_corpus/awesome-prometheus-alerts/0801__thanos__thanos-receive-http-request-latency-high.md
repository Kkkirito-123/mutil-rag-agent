# Thanos Receive Http Request Latency High

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-receiver`  
> Severity: **critical**  
> Duration (for): `10m`

## 现象 / Description

Thanos Receive {{$labels.job}} has a 99th percentile latency of {{ $value }} seconds for requests.

## PromQL 查询

```promql
(histogram_quantile(0.99, sum by (job, le) (rate(http_request_duration_seconds_bucket{job=~".*thanos-receive.*", handler="receive"}[5m]))) > 10 and sum by (job) (rate(http_request_duration_seconds_count{job=~".*thanos-receive.*", handler="receive"}[5m])) > 0)
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Thanos
