# MySQL InnoDB log waits

> Group: **Databases**  
> Service: **MySQL**  
> Exporter: `mysqld-exporter`  
> Severity: **warning**

## 现象 / Description

MySQL innodb log writes stalling ({{ $value }} waits/s)

## PromQL 查询

```promql
deriv(mysql_global_status_innodb_log_waits[15m]) > 10
```

## 处理建议 / Comments

mysqld_exporter exposes SHOW GLOBAL STATUS variables as untyped/gauge, so deriv() is used instead of rate().

## 故障定位

- 触发该告警时, 检查 MySQL 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / MySQL
