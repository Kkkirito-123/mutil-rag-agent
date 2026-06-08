# CouchDB critical log entries

> Group: **Databases**  
> Service: **CouchDB**  
> Exporter: `gesellix-couchdb-prometheus-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Critical or error log entries detected in the last 5 minutes

## PromQL 查询

```promql
increase(couchdb_server_couch_log{level=~"error|critical"}[5m]) > 5
```

## 故障定位

- 触发该告警时, 检查 CouchDB 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / CouchDB
