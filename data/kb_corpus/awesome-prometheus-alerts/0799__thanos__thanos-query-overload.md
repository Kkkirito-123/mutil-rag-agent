# Thanos Query Overload

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-query`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

Thanos Query {{$labels.job}} has been overloaded for more than 15 minutes. This may be a symptom of excessive simultanous complex requests, low performance of the Prometheus API, or failures within these components. Assess the health of the Thanos query instances, the connnected Prometheus instances, look for potential senders of these requests and then contact support.

## PromQL 查询

```promql
(max_over_time(thanos_query_concurrent_gate_queries_max[5m]) - avg_over_time(thanos_query_concurrent_gate_queries_in_flight[5m]) < 1)
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Thanos
