# MySQL restarted

> Group: **Databases**  
> Service: **MySQL**  
> Exporter: `mysqld-exporter`  
> Severity: **info**

## 现象 / Description

MySQL has just been restarted, less than one minute ago on {{ $labels.instance }}.

## PromQL 查询

```promql
mysql_global_status_uptime < 60
```

## 故障定位

- 触发该告警时, 检查 MySQL 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Databases / MySQL
