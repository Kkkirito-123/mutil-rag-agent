# GitLab Gitaly high gRPC error rate

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitaly`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Gitaly on {{ $labels.instance }} is returning more than 5% gRPC errors.

## PromQL 查询

```promql
sum(rate(grpc_server_handled_total{job="gitaly",grpc_code=~"Internal|Unavailable|DeadlineExceeded|ResourceExhausted|Aborted|Unknown|DataLoss"}[5m])) / sum(rate(grpc_server_handled_total{job="gitaly"}[5m])) * 100 > 5 and sum(rate(grpc_server_handled_total{job="gitaly"}[5m])) > 0
```

## 处理建议 / Comments

Filters to actual error codes. grpc_code!="OK" includes benign codes like NotFound, AlreadyExists, and Cancelled.

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
