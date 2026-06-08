# CouchDB Mango queries failed due to invalid index

> Group: **Databases**  
> Service: **CouchDB**  
> Exporter: `gesellix-couchdb-prometheus-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Some Mango queries failed to execute because the index was missing or invalid

## PromQL 查询

```promql
rate(couchdb_mango_query_invalid_index[5m]) > 5
```

## 故障定位

- 触发该告警时, 检查 CouchDB 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / CouchDB
