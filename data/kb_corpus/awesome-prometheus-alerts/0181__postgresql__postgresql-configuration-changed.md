# Postgresql configuration changed

> Group: **Databases**  
> Service: **PostgreSQL**  
> Exporter: `postgres-exporter`  
> Severity: **info**

## 现象 / Description

Postgres Database configuration change has occurred

## PromQL 查询

```promql
{__name__=~"pg_settings_.*",__name__!="pg_settings_transaction_read_only"} != ON(__name__, instance) {__name__=~"pg_settings_.*",__name__!="pg_settings_transaction_read_only"} OFFSET 5m
```

## 故障定位

- 触发该告警时, 检查 PostgreSQL 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Databases / PostgreSQL
