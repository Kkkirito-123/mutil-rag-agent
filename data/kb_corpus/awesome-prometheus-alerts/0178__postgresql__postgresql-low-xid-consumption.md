# Postgresql low XID consumption

> Group: **Databases**  
> Service: **PostgreSQL**  
> Exporter: `postgres-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Postgresql seems to be consuming transaction IDs very slowly

## PromQL 查询

```promql
rate(pg_txid_current[1m]) < 5
```

## 处理建议 / Comments

pg_txid_current is not a default postgres_exporter metric. You need to define a custom query. See https://github.com/samber/awesome-prometheus-alerts/issues/289#issuecomment-1164842737

## 故障定位

- 触发该告警时, 检查 PostgreSQL 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / PostgreSQL
