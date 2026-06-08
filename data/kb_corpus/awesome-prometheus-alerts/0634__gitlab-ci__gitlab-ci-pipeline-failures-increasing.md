# GitLab CI pipeline failures increasing

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitlab-built-in-exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

GitLab CI pipeline failures are increasing on {{ $labels.instance }} ({{ $value }}/s).

## PromQL 查询

```promql
deriv(gitlab_ci_pipeline_failure_reasons[5m]) > 0.05
```

## 处理建议 / Comments

This metric may not exist in all GitLab versions. Verify against your GitLab installation.

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
