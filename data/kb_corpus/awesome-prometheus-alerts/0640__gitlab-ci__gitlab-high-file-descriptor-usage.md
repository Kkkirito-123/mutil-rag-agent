# GitLab high file descriptor usage

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitlab-built-in-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

GitLab on {{ $labels.instance }} is using {{ $value }}% of available file descriptors.

## PromQL 查询

```promql
process_open_fds{job=~".*gitlab.*"} / process_max_fds * 100 > 80 and process_max_fds > 0
```

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
