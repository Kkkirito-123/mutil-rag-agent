# Nats server down

> Group: **Message brokers**  
> Service: **Nats**  
> Exporter: `nats-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

NATS server has been down for more than 5 minutes

## PromQL 查询

```promql
absent(up{job="nats"})
```

## 处理建议 / Comments

Replace job="nats" with the actual job name in your Prometheus configuration.

## 故障定位

- 触发该告警时, 检查 Nats 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Message brokers / Nats
