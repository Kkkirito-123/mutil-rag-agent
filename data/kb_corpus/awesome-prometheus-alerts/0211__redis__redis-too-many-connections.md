# Redis too many connections

> Group: **Databases**  
> Service: **Redis**  
> Exporter: `oliver006-redis-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Redis is running out of connections (> 90% used)

## PromQL 查询

```promql
redis_connected_clients / redis_config_maxclients * 100 > 90 and redis_config_maxclients > 0
```

## 故障定位

- 触发该告警时, 检查 Redis 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Redis
