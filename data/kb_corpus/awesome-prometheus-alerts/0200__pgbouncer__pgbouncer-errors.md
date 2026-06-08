# PGBouncer errors

> Group: **Databases**  
> Service: **PGBouncer**  
> Exporter: `spreaker-pgbouncer-exporter`  
> Severity: **warning**

## 现象 / Description

PGBouncer is logging errors. This may be due to a server restart or an admin typing commands at the pgbouncer console.

## PromQL 查询

```promql
increase(pgbouncer_errors_count{errmsg!="server conn crashed?"}[1m]) > 10
```

## 故障定位

- 触发该告警时, 检查 PGBouncer 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / PGBouncer
