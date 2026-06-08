# Redis missing master

> Group: **Databases**  
> Service: **Redis**  
> Exporter: `oliver006-redis-exporter`  
> Severity: **critical**

## 现象 / Description

Redis cluster has no node marked as master.

## PromQL 查询

```promql
(count(redis_instance_info{role="master"}) or vector(0)) < 1
```

## 故障定位

- 触发该告警时, 检查 Redis 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Redis
