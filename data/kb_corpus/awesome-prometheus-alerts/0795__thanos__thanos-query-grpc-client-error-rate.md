# Thanos Query Grpc Client Error Rate

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-query`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Thanos Query {{$labels.job}} is failing to send {{$value | humanize}}% of requests.

## PromQL 查询

```promql
(sum by (job) (rate(grpc_client_handled_total{grpc_code=~"Unknown|Internal|Unavailable|DataLoss|DeadlineExceeded|ResourceExhausted", job=~".*thanos-query.*"}[5m])) / sum by (job) (rate(grpc_client_started_total{job=~".*thanos-query.*"}[5m]))) * 100 > 5 and sum by (job) (rate(grpc_client_started_total{job=~".*thanos-query.*"}[5m])) > 0
```

## 处理建议 / Comments

Filters to actual error codes only. grpc_code!="OK" would include benign codes like NotFound, AlreadyExists, and Cancelled.

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Thanos
