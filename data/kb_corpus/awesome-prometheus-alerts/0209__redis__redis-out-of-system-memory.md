# Redis out of system memory

> Group: **Databases**  
> Service: **Redis**  
> Exporter: `oliver006-redis-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Redis is running out of system memory (> 90%)

## PromQL 查询

```promql
redis_memory_used_bytes / redis_total_system_memory_bytes * 100 > 90 and redis_total_system_memory_bytes > 0
```

## 处理建议 / Comments

The exporter must be started with --include-system-metrics flag or REDIS_EXPORTER_INCL_SYSTEM_METRICS=true environment variable.

## 故障定位

- 触发该告警时, 检查 Redis 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Redis
