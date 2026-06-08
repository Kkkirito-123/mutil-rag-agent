# GitLab Gitaly high RPC latency

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitaly`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Gitaly on {{ $labels.instance }} p95 unary RPC latency exceeds 1 second ({{ $value }}s).

## PromQL 查询

```promql
histogram_quantile(0.95, sum(rate(grpc_server_handling_seconds_bucket{job="gitaly",grpc_type="unary"}[5m])) by (le)) > 1
```

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
