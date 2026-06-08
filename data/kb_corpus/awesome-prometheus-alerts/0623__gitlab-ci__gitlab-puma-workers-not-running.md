# GitLab Puma workers not running

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitlab-built-in-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

GitLab Puma on {{ $labels.instance }} has {{ $value }} running workers out of expected total.

## PromQL 查询

```promql
puma_running_workers < puma_workers
```

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
