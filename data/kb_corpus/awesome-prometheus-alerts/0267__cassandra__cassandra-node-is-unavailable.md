# Cassandra Node is unavailable

> Group: **Databases**  
> Service: **Cassandra**  
> Exporter: `instaclustr-cassandra-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Cassandra Node is unavailable - {{ $labels.cassandra_cluster }} {{ $labels.exported_endpoint }}

## PromQL 查询

```promql
cassandra_endpoint_active < 1
```

## 处理建议 / Comments

1m delay allows a restart without triggering an alert.

## 故障定位

- 触发该告警时, 检查 Cassandra 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Cassandra
