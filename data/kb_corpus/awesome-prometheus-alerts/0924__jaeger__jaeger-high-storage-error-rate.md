# Jaeger high storage error rate

> Group: **Observability**  
> Service: **Jaeger**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Jaeger on {{ $labels.instance }} is experiencing {{ $value | humanize }}% storage errors on {{ $labels.operation }}.

## PromQL 查询

```promql
100 * sum(rate(jaeger_storage_requests_total{result="err"}[1m])) by (instance, job, namespace, operation) / sum(rate(jaeger_storage_requests_total[1m])) by (instance, job, namespace, operation) > 1 and sum(rate(jaeger_storage_requests_total[1m])) by (instance, job, namespace, operation) > 0
```

## 故障定位

- 触发该告警时, 检查 Jaeger 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Jaeger
