# Thanos Bucket Replicate Run Latency

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-bucket-replicate`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Thanos Replicate {{$labels.job}} has a 99th percentile latency of {{$value}} seconds for the replicate operations.

## PromQL 查询

```promql
(histogram_quantile(0.99, sum by (job, le) (rate(thanos_replicate_replication_run_duration_seconds_bucket[5m]))) > 20 and  sum by (job) (rate(thanos_replicate_replication_run_duration_seconds_count[5m])) > 0)
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Thanos
