# Cassandra client request read failure (Criteo)

> Group: **Databases**  
> Service: **Cassandra**  
> Exporter: `criteo-cassandra-exporter`  
> Severity: **critical**

## 现象 / Description

A lot of read failures encountered. A read failure is a non-timeout exception encountered during a read request. Examine the reason map to find to the root cause. The most common cause for this type of error is when batch sizes are too large.

## PromQL 查询

```promql
cassandra_stats{name="org:apache:cassandra:metrics:clientrequest:read:failures:oneminuterate"} > 0.05
```

## 故障定位

- 触发该告警时, 检查 Cassandra 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Cassandra
