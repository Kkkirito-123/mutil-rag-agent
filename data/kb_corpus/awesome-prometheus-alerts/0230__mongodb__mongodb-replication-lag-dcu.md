# MongoDB replication lag (DCU)

> Group: **Databases**  
> Service: **MongoDB**  
> Exporter: `dcu-mongodb-exporter`  
> Severity: **critical**

## 现象 / Description

Mongodb replication lag is more than 10s

## PromQL 查询

```promql
avg(mongodb_replset_member_optime_date{state="PRIMARY"}) - avg(mongodb_replset_member_optime_date{state="SECONDARY"}) > 10
```

## 故障定位

- 触发该告警时, 检查 MongoDB 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / MongoDB
