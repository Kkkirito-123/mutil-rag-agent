# Postgresql not enough connections

> Group: **Databases**  
> Service: **PostgreSQL**  
> Exporter: `postgres-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

PostgreSQL instance should have more connections (> 5)

## PromQL 查询

```promql
sum by (datname) (pg_stat_activity_count{datname!~"template.*|postgres"}) < 5
```

## 故障定位

- 触发该告警时, 检查 PostgreSQL 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / PostgreSQL
