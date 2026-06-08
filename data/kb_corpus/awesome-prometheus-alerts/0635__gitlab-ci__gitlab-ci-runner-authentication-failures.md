# GitLab CI runner authentication failures

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitlab-built-in-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

GitLab CI runners are experiencing authentication failures on {{ $labels.instance }} ({{ $value }} failures).

## PromQL 查询

```promql
increase(gitlab_ci_runner_authentication_failure_total[5m]) > 5
```

## 处理建议 / Comments

Frequent runner auth failures may indicate expired tokens or misconfigured runners.

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
