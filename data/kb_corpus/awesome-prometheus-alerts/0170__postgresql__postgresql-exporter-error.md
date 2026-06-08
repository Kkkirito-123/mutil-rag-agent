# Postgresql exporter error

> Group: **Databases**  
> Service: **PostgreSQL**  
> Exporter: `postgres-exporter`  
> Severity: **critical**

## 现象 / Description

Postgresql exporter is showing errors. A query may be buggy in query.yaml

## PromQL 查询

```promql
pg_exporter_last_scrape_error > 0
```

## 故障定位

- 触发该告警时, 检查 PostgreSQL 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / PostgreSQL
