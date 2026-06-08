# Oracle DB tablespace full (> 95%)

> Group: **Databases**  
> Service: **Oracle Database**  
> Exporter: `iamseth-oracledb-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Oracle Database tablespace {{ $labels.tablespace }} is critically full on {{ $labels.instance }} (current value: {{ $value }}%)

## PromQL 查询

```promql
oracledb_tablespace_used_percent > 95
```

## 故障定位

- 触发该告警时, 检查 Oracle Database 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Oracle Database
