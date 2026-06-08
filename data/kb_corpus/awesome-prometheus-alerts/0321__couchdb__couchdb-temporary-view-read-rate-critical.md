# CouchDB temporary view read rate critical

> Group: **Databases**  
> Service: **CouchDB**  
> Exporter: `gesellix-couchdb-prometheus-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Temporary view read rate exceeds 100 reads/sec, high risk of performance degradation

## PromQL 查询

```promql
rate(couchdb_httpd_temporary_view_reads[5m]) > 100
```

## 故障定位

- 触发该告警时, 检查 CouchDB 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / CouchDB
