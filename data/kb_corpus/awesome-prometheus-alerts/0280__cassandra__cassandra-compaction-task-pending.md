# Cassandra compaction task pending

> Group: **Databases**  
> Service: **Cassandra**  
> Exporter: `criteo-cassandra-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Many Cassandra compaction tasks are pending. You might need to increase I/O capacity by adding nodes to the cluster.

## PromQL 查询

```promql
cassandra_stats{name="org:apache:cassandra:metrics:compaction:pendingtasks:value"} > 100
```

## 故障定位

- 触发该告警时, 检查 Cassandra 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Cassandra
