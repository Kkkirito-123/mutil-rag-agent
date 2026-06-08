# Jaeger no storage reads succeeding

> Group: **Observability**  
> Service: **Jaeger**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Jaeger on {{ $labels.instance }} has no successful storage reads for {{ $labels.operation }} in the past 15 minutes.

## PromQL 查询

```promql
sum(increase(jaeger_storage_requests_total{result="ok"}[15m])) by (instance, job, namespace, operation) == 0 and sum(increase(jaeger_storage_requests_total[15m])) by (instance, job, namespace, operation) > 0
```

## 处理建议 / Comments

Fires when an operation (e.g. find_traces, get_services) has received requests but none succeeded.
May indicate a persistent storage error or a backend that is slow to recover.

## 故障定位

- 触发该告警时, 检查 Jaeger 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Jaeger
