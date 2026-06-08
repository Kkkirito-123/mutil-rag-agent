# Spinnaker API rate limit throttling

> Group: **CI/CD**  
> Service: **Spinnaker**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Gate is actively throttling API requests on {{ $labels.instance }} ({{ $value }} throttled requests per second).

## PromQL 查询

```promql
rate(rateLimitThrottling_total[5m]) > 0.05
```

## 故障定位

- 触发该告警时, 检查 Spinnaker 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / Spinnaker
