# Postgresql commit rate low

> Group: **Databases**  
> Service: **PostgreSQL**  
> Exporter: `postgres-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Postgresql seems to be processing very few transactions

## PromQL 查询

```promql
increase(pg_stat_database_xact_commit{datname!~"template.*|postgres",datid!="0"}[5m]) < 5
```

## 故障定位

- 触发该告警时, 检查 PostgreSQL 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / PostgreSQL
