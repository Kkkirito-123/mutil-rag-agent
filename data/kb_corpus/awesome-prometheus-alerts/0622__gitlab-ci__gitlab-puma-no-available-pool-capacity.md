# GitLab Puma no available pool capacity

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitlab-built-in-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

GitLab Puma pool capacity on {{ $labels.instance }} has been at 0 for 5 minutes. All threads are busy.

## PromQL 查询

```promql
puma_pool_capacity == 0
```

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
