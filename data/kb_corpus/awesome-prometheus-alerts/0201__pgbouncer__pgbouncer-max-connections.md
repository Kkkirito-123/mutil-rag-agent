# PGBouncer max connections

> Group: **Databases**  
> Service: **PGBouncer**  
> Exporter: `spreaker-pgbouncer-exporter`  
> Severity: **critical**

## 现象 / Description

The number of PGBouncer client connections has reached max_client_conn.

## PromQL 查询

```promql
increase(pgbouncer_errors_count{errmsg="no more connections allowed (max_client_conn)"}[2m]) > 0
```

## 故障定位

- 触发该告警时, 检查 PGBouncer 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / PGBouncer
