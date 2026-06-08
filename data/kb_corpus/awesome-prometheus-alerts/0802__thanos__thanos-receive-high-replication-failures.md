# Thanos Receive High Replication Failures

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-receiver`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Thanos Receive {{$labels.job}} is failing to replicate {{$value | humanize}}% of requests.

## PromQL 查询

```promql
thanos_receive_replication_factor > 1 and ((sum by (job) (rate(thanos_receive_replications_total{result="error"}[5m])) / sum by (job) (rate(thanos_receive_replications_total[5m]))) > (max by (job) (floor((thanos_receive_replication_factor+1)/ 2)) / max by (job) (thanos_receive_hashring_nodes))) * 100
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Thanos
