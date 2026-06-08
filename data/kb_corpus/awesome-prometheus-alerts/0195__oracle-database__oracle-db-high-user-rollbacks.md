# Oracle DB high user rollbacks

> Group: **Databases**  
> Service: **Oracle Database**  
> Exporter: `iamseth-oracledb-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Oracle Database on {{ $labels.instance }} has a high rollback rate ({{ $value }}% of transactions are rolled back)

## PromQL 查询

```promql
rate(oracledb_activity_user_rollbacks[5m]) / (rate(oracledb_activity_user_commits[5m]) + rate(oracledb_activity_user_rollbacks[5m])) * 100 > 20 and (rate(oracledb_activity_user_commits[5m]) + rate(oracledb_activity_user_rollbacks[5m])) > 0
```

## 处理建议 / Comments

A high rollback rate (>20%) often indicates application-level issues such as deadlocks, constraint violations, or poorly designed transactions.

## 故障定位

- 触发该告警时, 检查 Oracle Database 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Oracle Database
