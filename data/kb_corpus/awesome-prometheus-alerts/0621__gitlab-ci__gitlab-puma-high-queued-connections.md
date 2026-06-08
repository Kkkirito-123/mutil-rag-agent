# GitLab Puma high queued connections

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitlab-built-in-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

GitLab Puma has {{ $value }} queued connections on {{ $labels.instance }}. Requests are waiting for an available worker thread.

## PromQL 查询

```promql
puma_queued_connections > 5
```

## 处理建议 / Comments

Queued connections indicate Puma workers are saturated.
Consider increasing puma['worker_processes'] or puma['max_threads'] in gitlab.rb.

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
