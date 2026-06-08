# Cassandra client request unavailable write (Instaclustr)

> Group: **Databases**  
> Service: **Cassandra**  
> Exporter: `instaclustr-cassandra-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Some Cassandra client requests are unavailable to write - {{ $labels.cassandra_cluster }}

## PromQL 查询

```promql
changes(cassandra_client_request_unavailable_exceptions_total{operation="write"}[1m]) > 0
```

## 故障定位

- 触发该告警时, 检查 Cassandra 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Cassandra
