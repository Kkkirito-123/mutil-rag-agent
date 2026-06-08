# Spinnaker AWS rate limiting

> Group: **CI/CD**  
> Service: **Spinnaker**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Clouddriver is being rate-limited by AWS on {{ $labels.instance }} ({{ $value }}ms delay). Cloud operations will be slower.

## PromQL 查询

```promql
amazonClientProvider_rateLimitDelayMil > 1000
```

## 处理建议 / Comments

This metric is specific to AWS cloud providers in Clouddriver.
The 1000ms threshold is a rough default. Adjust based on your AWS usage patterns.

## 故障定位

- 触发该告警时, 检查 Spinnaker 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / Spinnaker
