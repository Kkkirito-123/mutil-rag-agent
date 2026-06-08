# GitLab Sidekiq high job completion time

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitlab-built-in-exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

GitLab Sidekiq job p95 completion time on {{ $labels.instance }} is above 5 minutes ({{ $value | humanizeDuration }}).

## PromQL 查询

```promql
histogram_quantile(0.95, sum(rate(sidekiq_jobs_completion_seconds_bucket[5m])) by (le, worker)) > 300
```

## 处理建议 / Comments

This metric requires the emit_sidekiq_histogram_metrics feature flag to be enabled.

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
