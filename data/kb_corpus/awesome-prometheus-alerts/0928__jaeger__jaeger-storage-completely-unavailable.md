# Jaeger storage completely unavailable

> Group: **Observability**  
> Service: **Jaeger**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Jaeger on {{ $labels.instance }} has 100% storage errors for {{ $labels.operation }} — storage backend may be down.

## PromQL 查询

```promql
sum(rate(jaeger_storage_requests_total{result="err"}[1m])) by (instance, job, namespace, operation) > 0 and sum(rate(jaeger_storage_requests_total{result="ok"}[1m])) by (instance, job, namespace, operation) == 0
```

## 处理建议 / Comments

Fires when all storage operations for a given type are failing and none are succeeding.
Indicates the storage backend (Cassandra, Elasticsearch, etc.) is likely unreachable or misconfigured.

## 故障定位

- 触发该告警时, 检查 Jaeger 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Jaeger
