# PGBouncer active connections

> Group: **Databases**  
> Service: **PGBouncer**  
> Exporter: `spreaker-pgbouncer-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

PGBouncer pools are filling up

## PromQL 查询

```promql
pgbouncer_pools_server_active_connections > 200
```

## 故障定位

- 触发该告警时, 检查 PGBouncer 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / PGBouncer
