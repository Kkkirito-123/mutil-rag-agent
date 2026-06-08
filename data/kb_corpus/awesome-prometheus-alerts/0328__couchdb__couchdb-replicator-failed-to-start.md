# CouchDB Replicator failed to start

> Group: **Databases**  
> Service: **CouchDB**  
> Exporter: `gesellix-couchdb-prometheus-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

One or more replication tasks failed to start

## PromQL 查询

```promql
increase(couchdb_replicator_failed_starts[5m]) > 0
```

## 故障定位

- 触发该告警时, 检查 CouchDB 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / CouchDB
