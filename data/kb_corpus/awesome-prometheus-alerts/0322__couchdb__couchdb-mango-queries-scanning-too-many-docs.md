# CouchDB Mango queries scanning too many docs

> Group: **Databases**  
> Service: **CouchDB**  
> Exporter: `gesellix-couchdb-prometheus-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Some Mango queries are scanning too many documents, consider adding indexes

## PromQL 查询

```promql
rate(couchdb_mango_too_many_docs_scanned[5m]) > 50
```

## 故障定位

- 触发该告警时, 检查 CouchDB 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / CouchDB
