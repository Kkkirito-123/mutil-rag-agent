# GitLab rack uncaught errors

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitlab-built-in-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

GitLab is experiencing uncaught errors in the Rack layer on {{ $labels.instance }} ({{ $value }}/s).

## PromQL 查询

```promql
rate(rack_uncaught_errors_total[5m]) > 0.05
```

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
