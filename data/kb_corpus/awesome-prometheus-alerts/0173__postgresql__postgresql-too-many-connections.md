# Postgresql too many connections

> Group: **Databases**  
> Service: **PostgreSQL**  
> Exporter: `postgres-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

PostgreSQL instance has too many connections (> 80%).

## PromQL 查询

```promql
sum by (instance, job, server) (pg_stat_activity_count) > min by (instance, job, server) (pg_settings_max_connections * 0.8)
```

## 故障定位

- 触发该告警时, 检查 PostgreSQL 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / PostgreSQL
