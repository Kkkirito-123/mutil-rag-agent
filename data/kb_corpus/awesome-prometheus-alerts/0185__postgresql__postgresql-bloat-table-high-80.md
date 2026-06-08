# Postgresql bloat table high (> 80%)

> Group: **Databases**  
> Service: **PostgreSQL**  
> Exporter: `postgres-exporter`  
> Severity: **warning**  
> Duration (for): `1h`

## 现象 / Description

The table {{ $labels.relname }} is bloated. You should execute `VACUUM {{ $labels.relname }};`

## PromQL 查询

```promql
pg_bloat_table_bloat_pct > 80 and on (relname) (pg_bloat_table_real_size > 200000000)
```

## 处理建议 / Comments

See https://github.com/samber/awesome-prometheus-alerts/issues/289#issuecomment-1164842737

## 故障定位

- 触发该告警时, 检查 PostgreSQL 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / PostgreSQL
