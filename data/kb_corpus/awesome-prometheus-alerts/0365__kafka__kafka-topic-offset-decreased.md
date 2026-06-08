# Kafka topic offset decreased

> Group: **Message brokers**  
> Service: **Kafka**  
> Exporter: `linkedin-kafka-exporter`  
> Severity: **warning**

## 现象 / Description

Kafka topic offset has decreased

## PromQL 查询

```promql
delta(kafka_burrow_partition_current_offset[1m]) < 0
```

## 故障定位

- 触发该告警时, 检查 Kafka 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / Kafka
