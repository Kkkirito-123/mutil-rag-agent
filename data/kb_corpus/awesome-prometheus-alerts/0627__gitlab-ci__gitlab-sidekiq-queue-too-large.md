# GitLab Sidekiq queue too large

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitlab-built-in-exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

GitLab Sidekiq has {{ $value }} running jobs, approaching concurrency limit on {{ $labels.instance }}.

## PromQL 查询

```promql
sum(sidekiq_running_jobs) >= sum(sidekiq_concurrency) * 0.9
```

## 处理建议 / Comments

When running jobs approach the concurrency limit, new jobs will queue up.
Consider scaling Sidekiq workers or increasing concurrency.

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
