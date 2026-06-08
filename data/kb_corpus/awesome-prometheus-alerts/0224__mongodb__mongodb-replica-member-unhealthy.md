# Mongodb replica member unhealthy

> Group: **Databases**  
> Service: **MongoDB**  
> Exporter: `percona-mongodb-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

MongoDB replica member is not healthy

## PromQL 查询

```promql
mongodb_rs_members_health == 0
```

## 处理建议 / Comments

1m delay allows a restart without triggering an alert.

## 故障定位

- 触发该告警时, 检查 MongoDB 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / MongoDB
