# GitLab version mismatch

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitlab-built-in-exporter`  
> Severity: **warning**

## 现象 / Description

Multiple GitLab versions are running across the fleet.

## PromQL 查询

```promql
count(count by (version) (gitlab_build_info)) > 1
```

## 处理建议 / Comments

This may happen during a rolling deployment. If it persists, investigate incomplete upgrades.

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
