# CouchDB replication cluster unstable

> Group: **Databases**  
> Service: **CouchDB**  
> Exporter: `gesellix-couchdb-prometheus-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

The replication cluster is unstable, replication may be interrupted

## PromQL 查询

```promql
couchdb_replicator_cluster_is_stable == 0
```

## 故障定位

- 触发该告警时, 检查 CouchDB 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / CouchDB
