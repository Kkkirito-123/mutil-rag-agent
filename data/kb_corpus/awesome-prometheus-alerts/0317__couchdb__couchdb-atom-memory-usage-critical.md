# CouchDB atom memory usage critical

> Group: **Databases**  
> Service: **CouchDB**  
> Exporter: `gesellix-couchdb-prometheus-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Atom memory usage is above 90% of limit

## PromQL 查询

```promql
couchdb_erlang_memory_atom_used > 0.9 * couchdb_erlang_memory_atom
```

## 故障定位

- 触发该告警时, 检查 CouchDB 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / CouchDB
