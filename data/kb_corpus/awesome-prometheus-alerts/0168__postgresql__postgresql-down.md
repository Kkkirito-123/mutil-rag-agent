# Postgresql down

> Group: **Databases**  
> Service: **PostgreSQL**  
> Exporter: `postgres-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Postgresql instance is down

## PromQL 查询

```promql
pg_up == 0
```

## 处理建议 / Comments

1m delay allows a restart without triggering an alert.

## 故障定位

- 触发该告警时, 检查 PostgreSQL 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / PostgreSQL
