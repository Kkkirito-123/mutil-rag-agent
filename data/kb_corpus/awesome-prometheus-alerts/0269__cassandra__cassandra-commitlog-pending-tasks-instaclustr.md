# Cassandra commitlog pending tasks (Instaclustr)

> Group: **Databases**  
> Service: **Cassandra**  
> Exporter: `instaclustr-cassandra-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Cassandra commitlog pending tasks - {{ $labels.cassandra_cluster }}

## PromQL 查询

```promql
cassandra_commit_log_pending_tasks > 15
```

## 故障定位

- 触发该告警时, 检查 Cassandra 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Cassandra
