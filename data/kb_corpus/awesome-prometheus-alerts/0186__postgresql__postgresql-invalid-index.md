# Postgresql invalid index

> Group: **Databases**  
> Service: **PostgreSQL**  
> Exporter: `postgres-exporter`  
> Severity: **warning**  
> Duration (for): `6h`

## 现象 / Description

The table {{ $labels.relname }} has an invalid index: {{ $labels.indexrelname }}. You should execute `DROP INDEX {{ $labels.indexrelname }};`

## PromQL 查询

```promql
pg_general_index_info_pg_relation_size{indexrelname=~".*ccnew.*"}
```

## 处理建议 / Comments

See https://github.com/samber/awesome-prometheus-alerts/issues/289#issuecomment-1164842737

## 故障定位

- 触发该告警时, 检查 PostgreSQL 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / PostgreSQL
