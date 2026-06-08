# Cassandra connection timeouts total (Criteo)

> Group: **Databases**  
> Service: **Cassandra**  
> Exporter: `criteo-cassandra-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Some connection between nodes are ending in timeout

## PromQL 查询

```promql
delta(cassandra_stats{name="org:apache:cassandra:metrics:connection:totaltimeouts:count"}[1m]) > 5
```

## 故障定位

- 触发该告警时, 检查 Cassandra 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Cassandra
