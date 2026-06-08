# Cassandra compaction executor blocked tasks (Criteo)

> Group: **Databases**  
> Service: **Cassandra**  
> Exporter: `criteo-cassandra-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Some Cassandra compaction executor tasks are blocked

## PromQL 查询

```promql
cassandra_stats{name="org:apache:cassandra:metrics:threadpools:internal:compactionexecutor:currentlyblockedtasks:count"} > 0
```

## 故障定位

- 触发该告警时, 检查 Cassandra 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Cassandra
