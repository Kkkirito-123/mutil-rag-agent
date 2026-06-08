# MySQL down

> Group: **Databases**  
> Service: **MySQL**  
> Exporter: `mysqld-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

MySQL instance is down on {{ $labels.instance }}

## PromQL 查询

```promql
mysql_up == 0
```

## 处理建议 / Comments

1m delay allows a restart without triggering an alert.

## 故障定位

- 触发该告警时, 检查 MySQL 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / MySQL
