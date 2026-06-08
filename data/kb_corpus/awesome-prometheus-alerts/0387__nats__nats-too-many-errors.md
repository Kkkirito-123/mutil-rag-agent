# Nats too many errors

> Group: **Message brokers**  
> Service: **Nats**  
> Exporter: `nats-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

NATS server has encountered {{ $value }} JetStream API errors in the last 5 minutes

## PromQL 查询

```promql
increase(gnatsd_varz_jetstream_stats_api_errors[5m]) > 5
```

## 故障定位

- 触发该告警时, 检查 Nats 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / Nats
