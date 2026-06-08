# RabbitMQ inactive exchange

> Group: **Message brokers**  
> Service: **RabbitMQ**  
> Exporter: `kbudde-rabbitmq-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Exchange receive less than 5 msgs per second

## PromQL 查询

```promql
rate(rabbitmq_exchange_messages_published_in_total{exchange="my-exchange"}[1m]) < 5
```

## 处理建议 / Comments

Indicate the exchange name in dedicated label.

## 故障定位

- 触发该告警时, 检查 RabbitMQ 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / RabbitMQ
