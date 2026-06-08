# CouchDB open OS files critical

> Group: **Databases**  
> Service: **CouchDB**  
> Exporter: `gesellix-couchdb-prometheus-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

CouchDB is using more than 90% of allowed OS file descriptors, may fail to open new files

## PromQL 查询

```promql
couchdb_httpd_open_os_files > 0.9 * 65535
```

## 处理建议 / Comments

Adjust 65535 to match your system's file descriptor limit (ulimit -n).

## 故障定位

- 触发该告警时, 检查 CouchDB 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / CouchDB
