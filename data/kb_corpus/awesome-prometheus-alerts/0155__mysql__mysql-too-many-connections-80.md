# MySQL too many connections (> 80%)

> Group: **Databases**  
> Service: **MySQL**  
> Exporter: `mysqld-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

More than 80% of MySQL connections are in use on {{ $labels.instance }}

## PromQL 查询

```promql
max_over_time(mysql_global_status_threads_connected[1m]) / mysql_global_variables_max_connections * 100 > 80 and mysql_global_variables_max_connections > 0
```

## 故障定位

- 触发该告警时, 检查 MySQL 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / MySQL
