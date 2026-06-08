# RabbitMQ no queue consumer

> Group: **Message brokers**  
> Service: **RabbitMQ**  
> Exporter: `rabbitmq-exporter`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

A queue has less than 1 consumer

## PromQL 查询

```promql
rabbitmq_queue_consumers < 1
```

## 故障定位

- 触发该告警时, 检查 RabbitMQ 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / RabbitMQ
