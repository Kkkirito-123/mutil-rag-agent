# Jaeger query service high error rate

> Group: **Observability**  
> Service: **Jaeger**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Jaeger query service on {{ $labels.instance }} is returning {{ $value | humanize }}% HTTP 5xx errors.

## PromQL 查询

```promql
100 * sum(rate(http_server_request_duration_seconds_count{http_route="/api/traces",http_response_status_code=~"5.."}[1m])) by (instance, job, namespace) / sum(rate(http_server_request_duration_seconds_count{http_route="/api/traces"}[1m])) by (instance, job, namespace) > 1 and sum(rate(http_server_request_duration_seconds_count{http_route="/api/traces"}[1m])) by (instance, job, namespace) > 0
```

## 处理建议 / Comments

Filters on http_route="/api/traces" (the trace search endpoint). The http_server_request_duration_seconds
metric is emitted by the otelhttp middleware used by the Jaeger query service.

## 故障定位

- 触发该告警时, 检查 Jaeger 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Jaeger
