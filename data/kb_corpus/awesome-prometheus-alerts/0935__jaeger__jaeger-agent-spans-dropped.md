# Jaeger agent spans dropped

> Group: **Observability**  
> Service: **Jaeger**  
> Exporter: `embedded-exporter-legacy`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

Jaeger agent on {{ $labels.instance }} is dropping {{ $value | humanize }}% of span batches.

## PromQL 查询

```promql
100 * sum(rate(jaeger_agent_reporter_batches_failures_total[1m])) by (instance, job, namespace) / sum(rate(jaeger_agent_reporter_batches_submitted_total[1m])) by (instance, job, namespace) > 1 and sum(rate(jaeger_agent_reporter_batches_submitted_total[1m])) by (instance, job, namespace) > 0
```

## 故障定位

- 触发该告警时, 检查 Jaeger 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Jaeger
