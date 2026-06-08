# Cassandra storage exceptions (Criteo)

> Group: **Databases**  
> Service: **Cassandra**  
> Exporter: `criteo-cassandra-exporter`  
> Severity: **critical**

## 现象 / Description

Something is going wrong with cassandra storage

## PromQL 查询

```promql
changes(cassandra_stats{name="org:apache:cassandra:metrics:storage:exceptions:count"}[1m]) > 1
```

## 故障定位

- 触发该告警时, 检查 Cassandra 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Cassandra
