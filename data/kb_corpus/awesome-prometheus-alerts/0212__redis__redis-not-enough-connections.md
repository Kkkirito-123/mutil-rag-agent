# Redis not enough connections

> Group: **Databases**  
> Service: **Redis**  
> Exporter: `oliver006-redis-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Redis instance should have more connections (> 5)

## PromQL 查询

```promql
redis_connected_clients < 5
```

## 故障定位

- 触发该告警时, 检查 Redis 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Redis
