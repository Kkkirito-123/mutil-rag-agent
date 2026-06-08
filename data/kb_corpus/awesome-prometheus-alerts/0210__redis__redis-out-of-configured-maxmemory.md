# Redis out of configured maxmemory

> Group: **Databases**  
> Service: **Redis**  
> Exporter: `oliver006-redis-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Redis is running out of configured maxmemory (> 90%)

## PromQL 查询

```promql
redis_memory_used_bytes / redis_memory_max_bytes * 100 > 90 and on(instance) redis_memory_max_bytes > 0
```

## 故障定位

- 触发该告警时, 检查 Redis 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Redis
