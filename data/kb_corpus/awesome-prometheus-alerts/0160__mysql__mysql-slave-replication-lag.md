# MySQL Slave replication lag

> Group: **Databases**  
> Service: **MySQL**  
> Exporter: `mysqld-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

MySQL replication lag on {{ $labels.instance }}

## PromQL 查询

```promql
( (mysql_slave_status_seconds_behind_master - mysql_slave_status_sql_delay) and ON (instance) mysql_slave_status_master_server_id > 0 ) > 30
```

## 故障定位

- 触发该告警时, 检查 MySQL 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / MySQL
