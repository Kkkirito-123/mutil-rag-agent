# GitLab high HTTP request latency

> Group: **CI/CD**  
> Service: **GitLab CI**  
> Exporter: `gitlab-built-in-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

GitLab p95 HTTP request latency on {{ $labels.instance }} is above 10 seconds.

## PromQL 查询

```promql
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 10
```

## 处理建议 / Comments

Threshold of 10s may need adjustment based on your instance size and workload.

## 故障定位

- 触发该告警时, 检查 GitLab CI 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / GitLab CI
