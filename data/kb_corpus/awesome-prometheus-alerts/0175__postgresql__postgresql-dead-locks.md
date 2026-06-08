# Postgresql dead locks

> Group: **Databases**  
> Service: **PostgreSQL**  
> Exporter: `postgres-exporter`  
> Severity: **warning**

## 现象 / Description

PostgreSQL has dead-locks ({{ $value }} in the last minute)

## PromQL 查询

```promql
increase(pg_stat_database_deadlocks{datname!~"template.*|postgres",datid!="0"}[1m]) > 5
```

## 故障定位

- 触发该告警时, 检查 PostgreSQL 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / PostgreSQL
