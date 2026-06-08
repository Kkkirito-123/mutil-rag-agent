# Jaeger slow storage operations

> Group: **Observability**  
> Service: **Jaeger**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Jaeger on {{ $labels.instance }} storage p99 latency for {{ $labels.operation }} is {{ $value | humanizeDuration }}.

## PromQL 查询

```promql
histogram_quantile(0.99, sum(rate(jaeger_storage_latency_seconds_bucket[5m])) by (le, instance, job, namespace, operation)) > 1
```

## 处理建议 / Comments

Threshold of 1s is a rough default. Adjust based on your storage backend and data volume.

## 故障定位

- 触发该告警时, 检查 Jaeger 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Jaeger
