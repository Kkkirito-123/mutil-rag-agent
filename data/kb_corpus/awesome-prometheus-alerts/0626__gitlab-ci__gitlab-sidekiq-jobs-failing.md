# GitLab Sidekiq jobs failing

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitlab-built-in-exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

GitLab Sidekiq jobs are failing at a rate of {{ $value }} per second on {{ $labels.instance }}.

## PromQL 查询

```promql
rate(sidekiq_jobs_failed_total[5m]) > 0.1
```

## 处理建议 / Comments

This metric requires the emit_sidekiq_histogram_metrics feature flag to be enabled.
A sustained failure rate indicates background processing issues.

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
