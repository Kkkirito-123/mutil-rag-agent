# GitLab Gitaly authentication failures

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitaly`  
> Severity: **warning**

## 现象 / Description

Gitaly on {{ $labels.instance }} has authentication failures ({{ $value }}).

## PromQL 查询

```promql
increase(gitaly_authentications_total{status="failed"}[5m]) > 3
```

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
