# RabbitMQ cluster partition

> Group: **Message brokers**  
> Service: **RabbitMQ**  
> Exporter: `kbudde-rabbitmq-exporter`  
> Severity: **critical**

## 现象 / Description

RabbitMQ cluster has a network partition ({{ $value }} partitions detected). Messages may be lost or duplicated.

## PromQL 查询

```promql
rabbitmq_partitions > 0
```

## 故障定位

- 触发该告警时, 检查 RabbitMQ 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Message brokers / RabbitMQ
