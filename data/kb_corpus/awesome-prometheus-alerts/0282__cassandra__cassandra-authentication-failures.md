# Cassandra authentication failures

> Group: **Databases**  
> Service: **Cassandra**  
> Exporter: `criteo-cassandra-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Increase of Cassandra authentication failures

## PromQL 查询

```promql
delta(cassandra_stats{name="org:apache:cassandra:metrics:client:authfailure:count"}[1m]) > 5
```

## 故障定位

- 触发该告警时, 检查 Cassandra 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Cassandra
