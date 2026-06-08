# MySQL too many open files

> Group: **Databases**  
> Service: **MySQL**  
> Exporter: `mysqld-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

MySQL has too many open files, consider increase variables open_files_limit on {{ $labels.instance }}.

## PromQL 查询

```promql
mysql_global_status_innodb_num_open_files / mysql_global_variables_open_files_limit * 100 > 75 and mysql_global_variables_open_files_limit > 0
```

## 故障定位

- 触发该告警时, 检查 MySQL 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / MySQL
