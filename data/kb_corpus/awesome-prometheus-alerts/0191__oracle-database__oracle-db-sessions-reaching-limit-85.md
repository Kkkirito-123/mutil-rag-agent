# Oracle DB sessions reaching limit (> 85%)

> Group: **Databases**  
> Service: **Oracle Database**  
> Exporter: `iamseth-oracledb-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Oracle Database session utilization is above 85% on {{ $labels.instance }} (current value: {{ $value }}%)

## PromQL 查询

```promql
oracledb_resource_current_utilization{resource_name="sessions"} / oracledb_resource_limit_value{resource_name="sessions"} * 100 > 85 and oracledb_resource_limit_value{resource_name="sessions"} > 0
```

## 处理建议 / Comments

Threshold is workload-dependent. Adjust 85% to suit your environment.

## 故障定位

- 触发该告警时, 检查 Oracle Database 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Oracle Database
