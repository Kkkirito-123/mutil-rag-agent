# GitLab Gitaly resource exhausted

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitaly`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Gitaly on {{ $labels.instance }} is returning ResourceExhausted errors, indicating overload ({{ $value }}%).

## PromQL 查询

```promql
sum(rate(grpc_server_handled_total{job="gitaly",grpc_code="ResourceExhausted"}[5m])) / sum(rate(grpc_server_handled_total{job="gitaly"}[5m])) * 100 > 1 and sum(rate(grpc_server_handled_total{job="gitaly"}[5m])) > 0
```

## 处理建议 / Comments

ResourceExhausted errors from Gitaly mean Git operations are being rejected due to
concurrency limits. This directly impacts users trying to push, pull, or clone.

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
