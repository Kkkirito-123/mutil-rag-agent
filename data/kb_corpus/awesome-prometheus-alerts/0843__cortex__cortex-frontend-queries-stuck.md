# Cortex frontend queries stuck

> Group: **Observability**  
> Service: **Cortex**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

There are queued up queries in query-frontend.

## PromQL 查询

```promql
sum by (job) (cortex_query_frontend_queue_length) > 0
```

## 故障定位

- 触发该告警时, 检查 Cortex 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Cortex
