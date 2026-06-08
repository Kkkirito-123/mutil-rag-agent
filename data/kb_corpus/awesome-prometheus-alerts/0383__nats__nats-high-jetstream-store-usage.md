# Nats high JetStream store usage

> Group: **Message brokers**  
> Service: **Nats**  
> Exporter: `nats-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

JetStream store usage is over 80%

## PromQL 查询

```promql
gnatsd_varz_jetstream_stats_storage / gnatsd_varz_jetstream_config_max_storage > 0.8 and gnatsd_varz_jetstream_config_max_storage > 0
```

## 故障定位

- 触发该告警时, 检查 Nats 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / Nats
