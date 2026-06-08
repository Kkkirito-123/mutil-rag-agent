# Postgresql high rollback rate

> Group: **Databases**  
> Service: **PostgreSQL**  
> Exporter: `postgres-exporter`  
> Severity: **warning**

## 现象 / Description

Ratio of transactions being aborted compared to committed is > 2 %

## PromQL 查询

```promql
sum by (namespace,datname,instance) (rate(pg_stat_database_xact_rollback{datname!~"template.*|postgres",datid!="0"}[3m])) / (sum by (namespace,datname,instance) (rate(pg_stat_database_xact_rollback{datname!~"template.*|postgres",datid!="0"}[3m])) + sum by (namespace,datname,instance) (rate(pg_stat_database_xact_commit{datname!~"template.*|postgres",datid!="0"}[3m]))) > 0.02 and (sum by (namespace,datname,instance) (rate(pg_stat_database_xact_rollback{datname!~"template.*|postgres",datid!="0"}[3m])) + sum by (namespace,datname,instance) (rate(pg_stat_database_xact_commit{datname!~"template.*|postgres",datid!="0"}[3m]))) > 0
```

## 故障定位

- 触发该告警时, 检查 PostgreSQL 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / PostgreSQL
