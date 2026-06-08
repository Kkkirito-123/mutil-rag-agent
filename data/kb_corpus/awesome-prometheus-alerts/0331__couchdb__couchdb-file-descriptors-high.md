# CouchDB file descriptors high

> Group: **Databases**  
> Service: **CouchDB**  
> Exporter: `gesellix-couchdb-prometheus-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Process is using more than 85% of allowed file descriptors

## PromQL 查询

```promql
process_open_fds / process_max_fds > 0.85 and process_max_fds > 0
```

## 故障定位

- 触发该告警时, 检查 CouchDB 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / CouchDB
