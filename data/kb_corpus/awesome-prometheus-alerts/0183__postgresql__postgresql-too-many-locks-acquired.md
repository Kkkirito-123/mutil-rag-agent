# Postgresql too many locks acquired

> Group: **Databases**  
> Service: **PostgreSQL**  
> Exporter: `postgres-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Too many locks acquired on the database. If this alert happens frequently, we may need to increase the postgres setting max_locks_per_transaction.

## PromQL 查询

```promql
((sum by (instance) (pg_locks_count)) / (pg_settings_max_locks_per_transaction * pg_settings_max_connections)) > 0.20 and (pg_settings_max_locks_per_transaction * pg_settings_max_connections) > 0
```

## 故障定位

- 触发该告警时, 检查 PostgreSQL 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / PostgreSQL
