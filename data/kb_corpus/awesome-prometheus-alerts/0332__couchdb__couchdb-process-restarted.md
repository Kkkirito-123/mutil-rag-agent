# CouchDB process restarted

> Group: **Databases**  
> Service: **CouchDB**  
> Exporter: `gesellix-couchdb-prometheus-exporter`  
> Severity: **info**  
> Duration (for): `1m`

## 现象 / Description

CouchDB process has restarted recently

## PromQL 查询

```promql
changes(process_start_time_seconds[1h]) > 0
```

## 故障定位

- 触发该告警时, 检查 CouchDB 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Databases / CouchDB
