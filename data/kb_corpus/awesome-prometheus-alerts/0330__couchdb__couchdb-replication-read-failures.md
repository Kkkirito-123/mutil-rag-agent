# CouchDB replication read failures

> Group: **Databases**  
> Service: **CouchDB**  
> Exporter: `gesellix-couchdb-prometheus-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Replication changes feed has failed reads more than 5 times in 5 minutes

## PromQL 查询

```promql
increase(couchdb_replicator_changes_read_failures[5m]) > 5
```

## 故障定位

- 触发该告警时, 检查 CouchDB 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / CouchDB
