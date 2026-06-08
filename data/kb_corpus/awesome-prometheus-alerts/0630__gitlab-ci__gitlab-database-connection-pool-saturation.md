# GitLab database connection pool saturation

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitlab-built-in-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

GitLab database connection pool on {{ $labels.instance }} ({{ $labels.class }}) is {{ $value }}% busy.

## PromQL 查询

```promql
gitlab_database_connection_pool_busy / gitlab_database_connection_pool_size * 100 > 90 and gitlab_database_connection_pool_size > 0
```

## 处理建议 / Comments

When the pool is near saturation, requests may block waiting for a connection.
Increase db_pool_size in gitlab.rb or investigate slow queries.

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
