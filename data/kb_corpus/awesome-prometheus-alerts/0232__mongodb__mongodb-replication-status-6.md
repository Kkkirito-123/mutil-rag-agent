# MongoDB replication Status 6

> Group: **Databases**  
> Service: **MongoDB**  
> Exporter: `dcu-mongodb-exporter`  
> Severity: **critical**

## 现象 / Description

MongoDB Replication set member as seen from another member of the set, is not yet known

## PromQL 查询

```promql
mongodb_replset_member_state == 6
```

## 故障定位

- 触发该告警时, 检查 MongoDB 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / MongoDB
