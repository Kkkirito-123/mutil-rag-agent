# Redis cluster flapping

> Group: **Databases**  
> Service: **Redis**  
> Exporter: `oliver006-redis-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Changes have been detected in Redis replica connection. This can occur when replica nodes lose connection to the master and reconnect (a.k.a flapping).

## PromQL 查询

```promql
changes(redis_connected_slaves[1m]) > 1
```

## 故障定位

- 触发该告警时, 检查 Redis 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Redis
