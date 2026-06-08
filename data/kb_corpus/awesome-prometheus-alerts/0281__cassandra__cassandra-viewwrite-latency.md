# Cassandra viewwrite latency

> Group: **Databases**  
> Service: **Cassandra**  
> Exporter: `criteo-cassandra-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

High viewwrite latency on {{ $labels.instance }} cassandra node

## PromQL 查询

```promql
cassandra_stats{name="org:apache:cassandra:metrics:clientrequest:viewwrite:viewwritelatency:99thpercentile"} > 100000
```

## 故障定位

- 触发该告警时, 检查 Cassandra 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Cassandra
