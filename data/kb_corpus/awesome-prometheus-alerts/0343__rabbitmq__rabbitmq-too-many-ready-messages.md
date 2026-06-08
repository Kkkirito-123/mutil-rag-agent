# RabbitMQ too many ready messages

> Group: **Message brokers**  
> Service: **RabbitMQ**  
> Exporter: `rabbitmq-exporter`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

RabbitMQ too many ready messages on queue {{ $labels.queue }} ({{ $value }})

## PromQL 查询

```promql
sum(rabbitmq_queue_messages_ready) BY (queue) > 1000
```

## 故障定位

- 触发该告警时, 检查 RabbitMQ 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / RabbitMQ
