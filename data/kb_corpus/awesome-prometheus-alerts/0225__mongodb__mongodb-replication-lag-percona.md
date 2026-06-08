# MongoDB replication lag (Percona)

> Group: **Databases**  
> Service: **MongoDB**  
> Exporter: `percona-mongodb-exporter`  
> Severity: **critical**

## 现象 / Description

Mongodb replication lag is more than 10s

## PromQL 查询

```promql
(mongodb_rs_members_optimeDate{member_state="PRIMARY"} - on (set) group_right mongodb_rs_members_optimeDate{member_state="SECONDARY"}) / 1000 > 10
```

## 故障定位

- 触发该告警时, 检查 MongoDB 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / MongoDB
