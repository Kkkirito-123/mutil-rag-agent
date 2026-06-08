# RabbitMQ dead letter queue filling up

> Group: **Message brokers**  
> Service: **RabbitMQ**  
> Exporter: `kbudde-rabbitmq-exporter`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

Dead letter queue is filling up (> 10 msgs)

## PromQL 查询

```promql
rabbitmq_queue_messages{queue="my-dead-letter-queue"} > 10
```

## 处理建议 / Comments

Indicate the queue name in dedicated label.

## 故障定位

- 触发该告警时, 检查 RabbitMQ 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / RabbitMQ
