# RabbitMQ too many consumers

> Group: **Message brokers**  
> Service: **RabbitMQ**  
> Exporter: `kbudde-rabbitmq-exporter`  
> Severity: **critical**

## 现象 / Description

Queue should have only 1 consumer

## PromQL 查询

```promql
rabbitmq_queue_consumers{queue="my-queue"} > 1
```

## 处理建议 / Comments

Indicate the queue name in dedicated label.

## 故障定位

- 触发该告警时, 检查 RabbitMQ 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Message brokers / RabbitMQ
