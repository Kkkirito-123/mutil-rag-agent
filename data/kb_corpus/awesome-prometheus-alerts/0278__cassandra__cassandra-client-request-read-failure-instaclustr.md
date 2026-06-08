# Cassandra client request read failure (Instaclustr)

> Group: **Databases**  
> Service: **Cassandra**  
> Exporter: `instaclustr-cassandra-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Read failures have occurred, ensure there are not too many unavailable nodes - {{ $labels.cassandra_cluster }}

## PromQL 查询

```promql
increase(cassandra_client_request_failures_total{operation="read"}[1m]) > 5
```

## 故障定位

- 触发该告警时, 检查 Cassandra 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Cassandra
