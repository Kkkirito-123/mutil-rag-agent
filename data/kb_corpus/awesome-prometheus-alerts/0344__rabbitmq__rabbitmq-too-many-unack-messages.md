# RabbitMQ too many unack messages

> Group: **Message brokers**  
> Service: **RabbitMQ**  
> Exporter: `rabbitmq-exporter`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

Too many unacknowledged messages on queue {{ $labels.queue }} ({{ $value }})

## PromQL 查询

```promql
sum(rabbitmq_queue_messages_unacked) BY (queue) > 1000
```

## 故障定位

- 触发该告警时, 检查 RabbitMQ 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / RabbitMQ
