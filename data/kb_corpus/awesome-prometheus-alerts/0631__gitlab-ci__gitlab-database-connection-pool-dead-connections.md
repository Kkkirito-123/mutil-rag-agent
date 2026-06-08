# GitLab database connection pool dead connections

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitlab-built-in-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

GitLab database connection pool on {{ $labels.instance }} ({{ $labels.class }}) has {{ $value }} dead connections.

## PromQL 查询

```promql
gitlab_database_connection_pool_dead > 0
```

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
