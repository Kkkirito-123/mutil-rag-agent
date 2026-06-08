# RabbitMQ unroutable messages

> Group: **Message brokers**  
> Service: **RabbitMQ**  
> Exporter: `rabbitmq-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

A queue has unroutable messages ({{ $value }} in the last 5m)

## PromQL 查询

```promql
increase(rabbitmq_channel_messages_unroutable_returned_total[5m]) > 3 or increase(rabbitmq_channel_messages_unroutable_dropped_total[5m]) > 3
```

## 处理建议 / Comments

Threshold of 3 avoids noise from occasional misroutes. Adjust based on your expected traffic patterns.

## 故障定位

- 触发该告警时, 检查 RabbitMQ 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / RabbitMQ
