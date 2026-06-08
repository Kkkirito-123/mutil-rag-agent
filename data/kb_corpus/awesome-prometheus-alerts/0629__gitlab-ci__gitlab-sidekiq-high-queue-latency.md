# GitLab Sidekiq high queue latency

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitlab-built-in-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

GitLab Sidekiq jobs on {{ $labels.instance }} are waiting more than 60 seconds before being processed.

## PromQL 查询

```promql
histogram_quantile(0.95, sum(rate(sidekiq_jobs_queue_duration_seconds_bucket[5m])) by (le)) > 60
```

## 处理建议 / Comments

This metric requires the emit_sidekiq_histogram_metrics feature flag to be enabled.
High queue latency means jobs are stuck waiting. Check Sidekiq concurrency and queue sizes.

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
