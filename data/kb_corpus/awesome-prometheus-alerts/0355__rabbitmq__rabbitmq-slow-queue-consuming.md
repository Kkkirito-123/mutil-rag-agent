# RabbitMQ slow queue consuming

> Group: **Message brokers**  
> Service: **RabbitMQ**  
> Exporter: `kbudde-rabbitmq-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Queue messages are consumed slowly (> 60s)

## PromQL 查询

```promql
time() - rabbitmq_queue_head_message_timestamp{queue="my-queue"} > 60
```

## 处理建议 / Comments

Indicate the queue name in dedicated label.

## 故障定位

- 触发该告警时, 检查 RabbitMQ 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / RabbitMQ
