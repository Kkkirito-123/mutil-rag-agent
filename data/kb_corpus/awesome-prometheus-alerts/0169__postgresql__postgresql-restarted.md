# Postgresql restarted

> Group: **Databases**  
> Service: **PostgreSQL**  
> Exporter: `postgres-exporter`  
> Severity: **critical**

## 现象 / Description

Postgresql restarted

## PromQL 查询

```promql
time() - pg_postmaster_start_time_seconds < 60
```

## 故障定位

- 触发该告警时, 检查 PostgreSQL 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / PostgreSQL
