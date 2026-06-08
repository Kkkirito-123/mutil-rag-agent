# Postgresql too many dead tuples

> Group: **Databases**  
> Service: **PostgreSQL**  
> Exporter: `postgres-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

PostgreSQL dead tuples is too large

## PromQL 查询

```promql
((pg_stat_user_tables_n_dead_tup > 10000) / (pg_stat_user_tables_n_live_tup + pg_stat_user_tables_n_dead_tup)) >= 0.1 and (pg_stat_user_tables_n_live_tup + pg_stat_user_tables_n_dead_tup) > 0
```

## 故障定位

- 触发该告警时, 检查 PostgreSQL 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / PostgreSQL
