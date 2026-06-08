# Kafka consumer group lag

> Group: **Message brokers**  
> Service: **Kafka**  
> Exporter: `danielqsj-kafka-exporter`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

Kafka consumer group {{ $labels.consumergroup }} is lagging behind ({{ $value }} messages)

## PromQL 查询

```promql
sum(kafka_consumergroup_lag) by (consumergroup) > 10000
```

## 故障定位

- 触发该告警时, 检查 Kafka 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / Kafka
