# Cassandra connection timeouts total (Instaclustr)

> Group: **Databases**  
> Service: **Cassandra**  
> Exporter: `instaclustr-cassandra-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Some connection between nodes are ending in timeout - {{ $labels.cassandra_cluster }}

## PromQL 查询

```promql
sum by (cassandra_cluster,instance) (rate(cassandra_client_request_timeouts_total[5m])) > 5
```

## 故障定位

- 触发该告警时, 检查 Cassandra 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Cassandra
