# Redis missing backup

> Group: **Databases**  
> Service: **Redis**  
> Exporter: `oliver006-redis-exporter`  
> Severity: **critical**

## 现象 / Description

Redis has not been backed up for 48 hours

## PromQL 查询

```promql
time() - redis_rdb_last_save_timestamp_seconds > 60 * 60 * 48
```

## 故障定位

- 触发该告警时, 检查 Redis 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Redis
