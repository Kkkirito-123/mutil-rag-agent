# Redis rejected connections

> Group: **Databases**  
> Service: **Redis**  
> Exporter: `oliver006-redis-exporter`  
> Severity: **warning**

## 现象 / Description

Some connections to Redis has been rejected

## PromQL 查询

```promql
increase(redis_rejected_connections_total[1m]) > 5
```

## 故障定位

- 触发该告警时, 检查 Redis 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Redis
