# MySQL InnoDB history_len too long

> Group: **Databases**  
> Service: **MySQL**  
> Exporter: `mysqld-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

MySQL history_len (undo log) too long on {{ $labels.instance }}

## PromQL 查询

```promql
mysql_info_schema_innodb_metrics_transaction_trx_rseg_history_len > 50000
```

## 故障定位

- 触发该告警时, 检查 MySQL 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / MySQL
