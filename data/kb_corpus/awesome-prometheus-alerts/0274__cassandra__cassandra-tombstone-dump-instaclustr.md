# Cassandra tombstone dump (Instaclustr)

> Group: **Databases**  
> Service: **Cassandra**  
> Exporter: `instaclustr-cassandra-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Cassandra tombstone dump - {{ $labels.cassandra_cluster }}

## PromQL 查询

```promql
avg(cassandra_table_tombstones_scanned{quantile="0.99"}) by (instance,cassandra_cluster,keyspace) > 100
```

## 故障定位

- 触发该告警时, 检查 Cassandra 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Cassandra
