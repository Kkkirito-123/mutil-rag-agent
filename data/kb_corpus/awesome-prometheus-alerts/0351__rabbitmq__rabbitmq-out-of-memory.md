# RabbitMQ out of memory

> Group: **Message brokers**  
> Service: **RabbitMQ**  
> Exporter: `kbudde-rabbitmq-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Memory available for RabbitMQ is low (< 10%)

## PromQL 查询

```promql
rabbitmq_node_mem_used / rabbitmq_node_mem_limit * 100 > 90 and rabbitmq_node_mem_limit > 0
```

## 故障定位

- 触发该告警时, 检查 RabbitMQ 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / RabbitMQ
