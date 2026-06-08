# Cassandra node down

> Group: **Databases**  
> Service: **Cassandra**  
> Exporter: `criteo-cassandra-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Cassandra node down

## PromQL 查询

```promql
sum(cassandra_stats{name="org:apache:cassandra:net:failuredetector:downendpointcount"}) by (service,group,cluster,env) > 0
```

## 处理建议 / Comments

1m delay allows a restart without triggering an alert.

## 故障定位

- 触发该告警时, 检查 Cassandra 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Cassandra
