# ClickHouse distributed rejected inserts

> Group: **Databases**  
> Service: **Clickhouse**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

INSERTs into Distributed tables rejected due to pending bytes limit.

## PromQL 查询

```promql
increase(ClickHouseProfileEvents_DistributedRejectedInserts[5m]) > 3
```

## 故障定位

- 触发该告警时, 检查 Clickhouse 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Clickhouse
