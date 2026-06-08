# MySQL InnoDB Force Recovery is enabled

> Group: **Databases**  
> Service: **MySQL**  
> Exporter: `mysqld-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

MySQL InnoDB force recovery is enabled on {{ $labels.instance }}

## PromQL 查询

```promql
mysql_global_variables_innodb_force_recovery != 0
```

## 故障定位

- 触发该告警时, 检查 MySQL 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / MySQL
