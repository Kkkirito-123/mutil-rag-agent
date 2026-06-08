# Cassandra storage exceptions (Instaclustr)

> Group: **Databases**  
> Service: **Cassandra**  
> Exporter: `instaclustr-cassandra-exporter`  
> Severity: **critical**

## 现象 / Description

Something is going wrong with cassandra storage - {{ $labels.cassandra_cluster }}

## PromQL 查询

```promql
changes(cassandra_storage_exceptions_total[1m]) > 1
```

## 故障定位

- 触发该告警时, 检查 Cassandra 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Cassandra
