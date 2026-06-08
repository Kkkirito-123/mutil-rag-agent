# RabbitMQ instances different versions

> Group: **Message brokers**  
> Service: **RabbitMQ**  
> Exporter: `rabbitmq-exporter`  
> Severity: **warning**  
> Duration (for): `1h`

## 现象 / Description

Running different version of RabbitMQ in the same cluster, can lead to failure.

## PromQL 查询

```promql
count(count(rabbitmq_build_info) by (rabbitmq_version)) > 1
```

## 故障定位

- 触发该告警时, 检查 RabbitMQ 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / RabbitMQ
