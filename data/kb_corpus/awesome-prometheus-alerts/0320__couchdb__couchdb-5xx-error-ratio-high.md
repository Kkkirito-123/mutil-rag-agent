# CouchDB 5xx error ratio high

> Group: **Databases**  
> Service: **CouchDB**  
> Exporter: `gesellix-couchdb-prometheus-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

More than 5% of HTTP requests are returning 5xx errors

## PromQL 查询

```promql
rate(couchdb_httpd_status_codes{code=~"5.."}[5m]) / rate(couchdb_httpd_requests[5m]) > 0.05 and rate(couchdb_httpd_requests[5m]) > 0
```

## 故障定位

- 触发该告警时, 检查 CouchDB 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / CouchDB
