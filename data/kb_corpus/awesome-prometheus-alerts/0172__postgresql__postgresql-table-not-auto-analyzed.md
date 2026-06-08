# Postgresql table not auto analyzed

> Group: **Databases**  
> Service: **PostgreSQL**  
> Exporter: `postgres-exporter`  
> Severity: **warning**

## 现象 / Description

Table {{ $labels.relname }} has not been auto analyzed for 10 days

## PromQL 查询

```promql
((pg_stat_user_tables_n_tup_del + pg_stat_user_tables_n_tup_upd + pg_stat_user_tables_n_tup_hot_upd) > pg_settings_autovacuum_analyze_threshold) and (time() - pg_stat_user_tables_last_autoanalyze) > 24 * 60 * 60 * 10
```

## 故障定位

- 触发该告警时, 检查 PostgreSQL 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / PostgreSQL
