# CouchDB node down

> Group: **Databases**  
> Service: **CouchDB**  
> Exporter: `gesellix-couchdb-prometheus-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

CouchDB node is not responding (node_up metric is 0) for more than 2 minutes

## PromQL 查询

```promql
couchdb_httpd_node_up == 0 or couchdb_httpd_up == 0
```

## 故障定位

- 触发该告警时, 检查 CouchDB 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / CouchDB
