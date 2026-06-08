# CouchDB Mango docs examined high

> Group: **Databases**  
> Service: **CouchDB**  
> Exporter: `gesellix-couchdb-prometheus-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

High number of documents examined per Mango queries, consider indexing

## PromQL 查询

```promql
rate(couchdb_mango_docs_examined[5m]) > 1000
```

## 故障定位

- 触发该告警时, 检查 CouchDB 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / CouchDB
