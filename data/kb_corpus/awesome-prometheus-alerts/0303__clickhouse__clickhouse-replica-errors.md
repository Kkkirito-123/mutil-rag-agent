# ClickHouse Replica Errors

> Group: **Databases**  
> Service: **Clickhouse**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Critical replica errors detected, either all replicas are stale or lost.

## PromQL 查询

```promql
ClickHouseErrorMetric_ALL_REPLICAS_ARE_STALE == 1 or ClickHouseErrorMetric_ALL_REPLICAS_LOST == 1
```

## 故障定位

- 触发该告警时, 检查 Clickhouse 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Clickhouse
