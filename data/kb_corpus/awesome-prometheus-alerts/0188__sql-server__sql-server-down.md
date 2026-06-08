# SQL Server down

> Group: **Databases**  
> Service: **SQL Server**  
> Exporter: `ozarklake-mssql-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

SQL server instance is down

## PromQL 查询

```promql
mssql_up == 0
```

## 处理建议 / Comments

1m delay allows a restart without triggering an alert.

## 故障定位

- 触发该告警时, 检查 SQL Server 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / SQL Server
