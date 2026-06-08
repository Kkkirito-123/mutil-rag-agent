# Oracle DB tablespace reaching capacity (> 85%)

> Group: **Databases**  
> Service: **Oracle Database**  
> Exporter: `iamseth-oracledb-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Oracle Database tablespace {{ $labels.tablespace }} is above 85% usage on {{ $labels.instance }} (current value: {{ $value }}%)

## PromQL 查询

```promql
oracledb_tablespace_used_percent > 85
```

## 故障定位

- 触发该告警时, 检查 Oracle Database 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Oracle Database
