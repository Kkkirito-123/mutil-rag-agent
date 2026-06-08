# Spinnaker dead messages

> Group: **CI/CD**  
> Service: **Spinnaker**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Orca is producing dead-lettered messages ({{ $value | humanize }}/s). These are tasks that exhausted all retries and will not be executed.

## PromQL 查询

```promql
rate(queue_dead_messages_total[5m]) > 0.05
```

## 故障定位

- 触发该告警时, 检查 Spinnaker 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / CI/CD / Spinnaker
