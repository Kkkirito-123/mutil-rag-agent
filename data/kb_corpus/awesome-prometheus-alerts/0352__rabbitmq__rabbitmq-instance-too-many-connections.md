# RabbitMQ instance too many connections

> Group: **Message brokers**  
> Service: **RabbitMQ**  
> Exporter: `kbudde-rabbitmq-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

RabbitMQ instance has too many connections (> 1000)

## PromQL 查询

```promql
rabbitmq_connections > 1000
```

## 故障定位

- 触发该告警时, 检查 RabbitMQ 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / RabbitMQ
