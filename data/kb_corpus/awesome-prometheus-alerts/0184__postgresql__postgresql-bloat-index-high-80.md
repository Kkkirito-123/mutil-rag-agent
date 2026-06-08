# Postgresql bloat index high (> 80%)

> Group: **Databases**  
> Service: **PostgreSQL**  
> Exporter: `postgres-exporter`  
> Severity: **warning**  
> Duration (for): `1h`

## 现象 / Description

The index {{ $labels.idxname }} is bloated. You should execute `REINDEX INDEX CONCURRENTLY {{ $labels.idxname }};`

## PromQL 查询

```promql
pg_bloat_btree_bloat_pct > 80 and on (idxname) (pg_bloat_btree_real_size > 100000000)
```

## 处理建议 / Comments

See https://github.com/samber/awesome-prometheus-alerts/issues/289#issuecomment-1164842737

## 故障定位

- 触发该告警时, 检查 PostgreSQL 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / PostgreSQL
