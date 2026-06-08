# GitLab Workhorse high in-flight requests

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `workhorse`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

GitLab Workhorse on {{ $labels.instance }} has {{ $value }} in-flight requests.

## PromQL 查询

```promql
gitlab_workhorse_http_in_flight_requests > 100
```

## 处理建议 / Comments

Threshold of 100 may need adjustment based on instance size.

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
