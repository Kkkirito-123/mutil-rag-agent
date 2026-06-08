# GitLab Workhorse high error rate

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `workhorse`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

GitLab Workhorse on {{ $labels.instance }} is returning more than 10% HTTP 5xx errors.

## PromQL 查询

```promql
sum(rate(gitlab_workhorse_http_request_duration_seconds_count{code=~"5.."}[5m])) / sum(rate(gitlab_workhorse_http_request_duration_seconds_count[5m])) * 100 > 10 and sum(rate(gitlab_workhorse_http_request_duration_seconds_count[5m])) > 0
```

## 处理建议 / Comments

Workhorse sits in front of Puma and handles Git HTTP, file uploads, and proxying.
Threshold from GitLab Omnibus default rules: 10% for high-traffic instances.

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
