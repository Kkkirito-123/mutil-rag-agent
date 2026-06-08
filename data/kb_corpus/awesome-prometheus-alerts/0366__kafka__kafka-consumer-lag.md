# Kafka consumer lag

> Group: **Message brokers**  
> Service: **Kafka**  
> Exporter: `linkedin-kafka-exporter`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

Kafka consumer has a 30 minutes and increasing lag

## PromQL 查询

```promql
kafka_burrow_topic_partition_offset - on(partition, cluster, topic) group_right() kafka_burrow_partition_current_offset >= (kafka_burrow_topic_partition_offset offset 15m - on(partition, cluster, topic) group_right() kafka_burrow_partition_current_offset offset 15m) AND kafka_burrow_topic_partition_offset - on(partition, cluster, topic) group_right() kafka_burrow_partition_current_offset > 0
```

## 故障定位

- 触发该告警时, 检查 Kafka 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / Kafka
