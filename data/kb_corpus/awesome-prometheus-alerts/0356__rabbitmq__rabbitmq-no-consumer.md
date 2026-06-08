# RabbitMQ no consumer

> Group: **Message brokers**  
> Service: **RabbitMQ**  
> Exporter: `kbudde-rabbitmq-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Queue has no consumer

## PromQL 查询

```promql
rabbitmq_queue_consumers == 0
```

## 处理建议 / Comments

Allows a short service restart.

## 故障定位

- 触发该告警时, 检查 RabbitMQ 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Message brokers / RabbitMQ
