# MySQL High QPS

> Group: **Databases**  
> Service: **MySQL**  
> Exporter: `mysqld-exporter`  
> Severity: **info**  
> Duration (for): `2m`

## 现象 / Description

MySQL is being overload with unusual QPS (> 10k QPS).

## PromQL 查询

```promql
deriv(mysql_global_status_questions[1m]) > 10000
```

## 处理建议 / Comments

mysqld_exporter exposes SHOW GLOBAL STATUS variables as untyped/gauge, so deriv() is used instead of irate().

## 故障定位

- 触发该告警时, 检查 MySQL 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Databases / MySQL
