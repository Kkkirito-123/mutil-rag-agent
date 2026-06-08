# Thanos Rule Grpc Error Rate

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-ruler`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Thanos Rule {{$labels.job}} is failing to handle {{$value | humanize}}% of requests.

## PromQL 查询

```promql
(sum by (job, instance) (rate(grpc_server_handled_total{grpc_code=~"Unknown|ResourceExhausted|Internal|Unavailable|DataLoss|DeadlineExceeded", job=~".*thanos-rule.*"}[5m]))/  sum by (job, instance) (rate(grpc_server_started_total{job=~".*thanos-rule.*"}[5m])) * 100 > 5) and sum by (job, instance) (rate(grpc_server_started_total{job=~".*thanos-rule.*"}[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Thanos
