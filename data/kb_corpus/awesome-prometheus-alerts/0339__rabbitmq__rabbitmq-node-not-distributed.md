# RabbitMQ node not distributed

> Group: **Message brokers**  
> Service: **RabbitMQ**  
> Exporter: `rabbitmq-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Distribution link to peer {{ $labels.peer }} is not 'up' (state {{ $value }})

## PromQL 查询

```promql
erlang_vm_dist_node_state < 3
```

## 处理建议 / Comments

1m delay allows a restart without triggering an alert.

## 故障定位

- 触发该告警时, 检查 RabbitMQ 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Message brokers / RabbitMQ
