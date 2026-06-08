# GitLab CI pipeline creation slow

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitlab-built-in-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

GitLab CI pipeline creation p95 latency on {{ $labels.instance }} is above 30 seconds.

## PromQL 查询

```promql
histogram_quantile(0.95, sum(rate(gitlab_ci_pipeline_creation_duration_seconds_bucket[5m])) by (le)) > 30
```

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
