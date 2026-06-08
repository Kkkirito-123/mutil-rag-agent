# Postgresql unused replication slot

> Group: **Databases**  
> Service: **PostgreSQL**  
> Exporter: `postgres-exporter`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

Unused Replication Slots

## PromQL 查询

```promql
(pg_replication_slots_active == 0) and (pg_replication_is_replica == 0)
```

## 故障定位

- 触发该告警时, 检查 PostgreSQL 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / PostgreSQL
