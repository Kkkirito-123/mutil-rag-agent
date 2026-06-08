# Cassandra tombstone dump (Criteo)

> Group: **Databases**  
> Service: **Cassandra**  
> Exporter: `criteo-cassandra-exporter`  
> Severity: **critical**

## 现象 / Description

Too much tombstones scanned in queries

## PromQL 查询

```promql
cassandra_stats{name="org:apache:cassandra:metrics:table:tombstonescannedhistogram:99thpercentile"} > 1000
```

## 故障定位

- 触发该告警时, 检查 Cassandra 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Cassandra
