# Postgresql replication lag

> Group: **Databases**  
> Service: **PostgreSQL**  
> Exporter: `postgres-exporter`  
> Severity: **warning**  
> Duration (for): `30s`

## 现象 / Description

The PostgreSQL replication lag is high (> 5s)

## PromQL 查询

```promql
pg_replication_lag_seconds > 5
```

## 故障定位

- 触发该告警时, 检查 PostgreSQL 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / PostgreSQL
