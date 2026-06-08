# Thanos Query High D N S Failures

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-query`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

Thanos Query {{$labels.job}} have {{$value | humanize}}% of failing DNS queries for store endpoints.

## PromQL 查询

```promql
(sum by (job) (rate(thanos_query_store_apis_dns_failures_total[5m])) / sum by (job) (rate(thanos_query_store_apis_dns_lookups_total[5m]))) * 100 > 1 and sum by (job) (rate(thanos_query_store_apis_dns_lookups_total[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Thanos
