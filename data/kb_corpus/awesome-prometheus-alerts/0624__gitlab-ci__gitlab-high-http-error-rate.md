# GitLab high HTTP error rate

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitlab-built-in-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

GitLab is returning more than 5% HTTP 5xx errors on {{ $labels.instance }}.

## PromQL 查询

```promql
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100 > 5 and sum(rate(http_requests_total[5m])) > 0
```

## 处理建议 / Comments

Threshold is 5% of all requests returning server errors.
Check GitLab logs at /var/log/gitlab/ for root cause.

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
