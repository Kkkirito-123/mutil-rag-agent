# MySQL slow queries

> Group: **Databases**  
> Service: **MySQL**  
> Exporter: `mysqld-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

MySQL server has some new slow queries ({{ $value }} in the last minute).

## PromQL 查询

```promql
delta(mysql_global_status_slow_queries[1m]) > 0
```

## 处理建议 / Comments

mysqld_exporter exposes SHOW GLOBAL STATUS variables as untyped/gauge, so delta() is used instead of increase().

## 故障定位

- 触发该告警时, 检查 MySQL 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / MySQL
