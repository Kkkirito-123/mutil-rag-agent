# MongoDB too many connections (DCU)

> Group: **Databases**  
> Service: **MongoDB**  
> Exporter: `dcu-mongodb-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Too many connections (> 80%)

## PromQL 查询

```promql
mongodb_connections{state="current"} / (mongodb_connections{state="current"} + mongodb_connections{state="available"}) * 100 > 80 and (mongodb_connections{state="current"} + mongodb_connections{state="available"}) > 0
```

## 故障定位

- 触发该告警时, 检查 MongoDB 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / MongoDB
