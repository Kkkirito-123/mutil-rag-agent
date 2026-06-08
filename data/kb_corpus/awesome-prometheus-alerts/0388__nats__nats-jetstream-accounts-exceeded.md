# Nats JetStream accounts exceeded

> Group: **Message brokers**  
> Service: **Nats**  
> Exporter: `nats-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

JetStream has more than 100 active accounts

## PromQL 查询

```promql
sum(gnatsd_varz_jetstream_stats_accounts) > 100
```

## 故障定位

- 触发该告警时, 检查 Nats 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / Nats
