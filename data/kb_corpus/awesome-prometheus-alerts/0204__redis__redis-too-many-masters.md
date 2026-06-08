# Redis too many masters

> Group: **Databases**  
> Service: **Redis**  
> Exporter: `oliver006-redis-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Redis cluster has too many nodes marked as master.

## PromQL 查询

```promql
count(redis_instance_info{role="master"}) > 1
```

## 处理建议 / Comments

1m delay allows a restart without triggering an alert.

## 故障定位

- 触发该告警时, 检查 Redis 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Redis
