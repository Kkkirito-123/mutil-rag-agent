# Cassandra cache hit rate key cache

> Group: **Databases**  
> Service: **Cassandra**  
> Exporter: `criteo-cassandra-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Key cache hit rate is below 85%

## PromQL 查询

```promql
cassandra_stats{name="org:apache:cassandra:metrics:cache:keycache:hitrate:value"} < .85
```

## 处理建议 / Comments

A low key cache hit rate increases disk I/O. Threshold is workload-dependent — adjust based on your data access patterns.

## 故障定位

- 触发该告警时, 检查 Cassandra 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Cassandra
