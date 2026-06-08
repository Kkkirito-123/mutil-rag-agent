# Cassandra many compaction tasks are pending

> Group: **Databases**  
> Service: **Cassandra**  
> Exporter: `instaclustr-cassandra-exporter`  
> Severity: **warning**

## 现象 / Description

Many Cassandra compaction tasks are pending - {{ $labels.cassandra_cluster }}

## PromQL 查询

```promql
cassandra_table_estimated_pending_compactions > 100
```

## 故障定位

- 触发该告警时, 检查 Cassandra 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Cassandra
