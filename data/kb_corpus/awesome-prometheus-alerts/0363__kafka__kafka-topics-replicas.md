# Kafka topics replicas

> Group: **Message brokers**  
> Service: **Kafka**  
> Exporter: `danielqsj-kafka-exporter`  
> Severity: **critical**

## 现象 / Description

Kafka topic {{ $labels.topic }} has fewer than 3 in-sync replicas ({{ $value }}), data durability is at risk.

## PromQL 查询

```promql
min(kafka_topic_partition_in_sync_replica) by (topic) < 3
```

## 故障定位

- 触发该告警时, 检查 Kafka 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Message brokers / Kafka
