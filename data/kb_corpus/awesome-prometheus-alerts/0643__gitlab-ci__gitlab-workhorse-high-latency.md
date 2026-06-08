# GitLab Workhorse high latency

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `workhorse`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

GitLab Workhorse on {{ $labels.instance }} p95 request latency is above 10 seconds.

## PromQL 查询

```promql
histogram_quantile(0.95, sum(rate(gitlab_workhorse_http_request_duration_seconds_bucket[5m])) by (le)) > 10
```

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
