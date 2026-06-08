# Thanos Bucket Replicate Error Rate

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-bucket-replicate`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Thanos Replicate is failing to run, {{$value | humanize}}% of attempts failed.

## PromQL 查询

```promql
(sum by (job) (rate(thanos_replicate_replication_runs_total{result="error"}[5m])) / on (job) group_left sum by (job) (rate(thanos_replicate_replication_runs_total[5m]))) * 100 >= 10 and sum by (job) (rate(thanos_replicate_replication_runs_total[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Thanos
