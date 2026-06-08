# CouchDB open databases critical

> Group: **Databases**  
> Service: **CouchDB**  
> Exporter: `gesellix-couchdb-prometheus-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Number of open databases exceeds 90% of node capacity

## PromQL 查询

```promql
couchdb_httpd_open_databases > 0.9 * 1000
```

## 处理建议 / Comments

The default max_dbs_open is 500. Adjust the threshold (currently 0.9 * 1000) to match your max_dbs_open setting.

## 故障定位

- 触发该告警时, 检查 CouchDB 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / CouchDB
