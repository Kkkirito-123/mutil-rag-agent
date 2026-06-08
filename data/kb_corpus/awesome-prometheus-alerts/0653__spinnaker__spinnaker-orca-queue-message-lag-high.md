# Spinnaker Orca queue message lag high

> Group: **CI/CD**  
> Service: **Spinnaker**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Orca queue message lag is {{ $value }}s. Pipeline stages are waiting too long before being processed.

## PromQL 查询

```promql
rate(queue_message_lag_seconds_sum[5m]) / rate(queue_message_lag_seconds_count[5m]) > 30 and rate(queue_message_lag_seconds_count[5m]) > 0
```

## 处理建议 / Comments

The 30s threshold is a rough default. Adjust based on your pipeline SLOs.

## 故障定位

- 触发该告警时, 检查 Spinnaker 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / CI/CD / Spinnaker
