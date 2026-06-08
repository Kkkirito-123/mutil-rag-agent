# Oracle DB too many active sessions

> Group: **Databases**  
> Service: **Oracle Database**  
> Exporter: `iamseth-oracledb-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Oracle Database on {{ $labels.instance }} has too many active user sessions (current value: {{ $value }})

## PromQL 查询

```promql
oracledb_sessions_value{status="ACTIVE", type="USER"} > 200
```

## 处理建议 / Comments

Threshold is highly workload-dependent. Adjust 200 to suit your environment.

## 故障定位

- 触发该告警时, 检查 Oracle Database 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Oracle Database
