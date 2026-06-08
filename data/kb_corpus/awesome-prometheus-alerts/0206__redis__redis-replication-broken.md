# Redis replication broken

> Group: **Databases**  
> Service: **Redis**  
> Exporter: `oliver006-redis-exporter`  
> Severity: **critical**

## 现象 / Description

Redis instance lost a slave

## PromQL 查询

```promql
delta(redis_connected_slaves[1m]) < 0
```

## 故障定位

- 触发该告警时, 检查 Redis 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Redis
