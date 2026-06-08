# Oracle DB high wait time (user I/O)

> Group: **Databases**  
> Service: **Oracle Database**  
> Exporter: `iamseth-oracledb-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Oracle Database on {{ $labels.instance }} is experiencing high user I/O wait time

## PromQL 查询

```promql
oracledb_wait_time_user_io > 300
```

## 处理建议 / Comments

The metric from v$waitclassmetric is already a normalized rate (centiseconds per second). Threshold 300 means 3 seconds of I/O wait per second of wall time.

## 故障定位

- 触发该告警时, 检查 Oracle Database 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Oracle Database
