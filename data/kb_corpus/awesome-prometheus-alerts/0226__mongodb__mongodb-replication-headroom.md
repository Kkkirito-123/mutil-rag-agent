# MongoDB replication headroom

> Group: **Databases**  
> Service: **MongoDB**  
> Exporter: `percona-mongodb-exporter`  
> Severity: **critical**

## 现象 / Description

MongoDB replication headroom is <= 0

## PromQL 查询

```promql
sum(avg(mongodb_mongod_replset_oplog_head_timestamp - mongodb_mongod_replset_oplog_tail_timestamp)) - sum(avg(mongodb_rs_members_optimeDate{member_state="PRIMARY"} - on (set) group_right mongodb_rs_members_optimeDate{member_state="SECONDARY"})) <= 0
```

## 处理建议 / Comments

This query mixes old (mongodb_mongod_*) and new (mongodb_rs_*) metric names. It requires the Percona exporter to run with --compatible-mode to expose both.

## 故障定位

- 触发该告警时, 检查 MongoDB 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / MongoDB
