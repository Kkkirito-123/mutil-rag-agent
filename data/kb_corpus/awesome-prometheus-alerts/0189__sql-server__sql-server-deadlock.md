# SQL Server deadlock

> Group: **Databases**  
> Service: **SQL Server**  
> Exporter: `ozarklake-mssql-exporter`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

SQL Server {{ $labels.instance }} is experiencing deadlocks ({{ $value }}/s)

## PromQL 查询

```promql
mssql_deadlocks > 5
```

## 故障定位

- 触发该告警时, 检查 SQL Server 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / SQL Server
