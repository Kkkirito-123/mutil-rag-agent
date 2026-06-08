# Postgresql SSL compression active

> Group: **Databases**  
> Service: **PostgreSQL**  
> Exporter: `postgres-exporter`  
> Severity: **warning**

## 现象 / Description

Database allows connections with SSL compression enabled. This may add significant jitter in replication delay. Replicas should turn off SSL compression via `sslcompression=0` in `recovery.conf`.

## PromQL 查询

```promql
sum by (instance) (pg_stat_ssl_compression) > 0
```

## 处理建议 / Comments

pg_stat_ssl_compression is not a default postgres_exporter metric and is only available on PostgreSQL 9.5-13 (removed in PG 14). See https://github.com/samber/awesome-prometheus-alerts/issues/289#issuecomment-1164842737

## 故障定位

- 触发该告警时, 检查 PostgreSQL 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / PostgreSQL
