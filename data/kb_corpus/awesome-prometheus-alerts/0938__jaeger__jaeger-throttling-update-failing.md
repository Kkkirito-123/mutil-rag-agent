# Jaeger throttling update failing

> Group: **Observability**  
> Service: **Jaeger**  
> Exporter: `embedded-exporter-legacy`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

Jaeger on {{ $labels.instance }} is failing {{ $value | humanize }}% of throttling policy updates.

## PromQL 查询

```promql
100 * sum(rate(jaeger_throttler_updates{result="err"}[1m])) by (instance, job, namespace) / sum(rate(jaeger_throttler_updates[1m])) by (instance, job, namespace) > 1 and sum(rate(jaeger_throttler_updates[1m])) by (instance, job, namespace) > 0
```

## 故障定位

- 触发该告警时, 检查 Jaeger 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Jaeger
