# RabbitMQ file descriptors usage

> Group: **Message brokers**  
> Service: **RabbitMQ**  
> Exporter: `rabbitmq-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

A node use more than 90% of file descriptors

## PromQL 查询

```promql
rabbitmq_process_open_fds / rabbitmq_process_max_fds * 100 > 90 and rabbitmq_process_max_fds > 0
```

## 故障定位

- 触发该告警时, 检查 RabbitMQ 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / RabbitMQ
