# RabbitMQ cluster down

> Group: **Message brokers**  
> Service: **RabbitMQ**  
> Exporter: `kbudde-rabbitmq-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Less than 3 nodes running in RabbitMQ cluster

## PromQL 查询

```promql
sum(rabbitmq_running) < 3
```

## 处理建议 / Comments

1m delay allows a restart without triggering an alert.

## 故障定位

- 触发该告警时, 检查 RabbitMQ 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Message brokers / RabbitMQ
