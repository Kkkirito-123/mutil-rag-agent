# MySQL high prepared statements utilization (> 80%)

> Group: **Databases**  
> Service: **MySQL**  
> Exporter: `mysqld-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

High utilization of prepared statements (>80%) on {{ $labels.instance }}

## PromQL 查询

```promql
max_over_time(mysql_global_status_prepared_stmt_count[1m]) / mysql_global_variables_max_prepared_stmt_count * 100 > 80 and mysql_global_variables_max_prepared_stmt_count > 0
```

## 故障定位

- 触发该告警时, 检查 MySQL 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / MySQL
