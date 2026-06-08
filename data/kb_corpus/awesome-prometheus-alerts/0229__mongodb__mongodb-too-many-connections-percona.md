# MongoDB too many connections (Percona)

> Group: **Databases**  
> Service: **MongoDB**  
> Exporter: `percona-mongodb-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Too many connections (> 80%)

## PromQL 查询

```promql
mongodb_ss_connections{conn_type="current"} / (mongodb_ss_connections{conn_type="current"} + mongodb_ss_connections{conn_type="available"}) * 100 > 80 and (mongodb_ss_connections{conn_type="current"} + mongodb_ss_connections{conn_type="available"}) > 0
```

## 故障定位

- 触发该告警时, 检查 MongoDB 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / MongoDB
