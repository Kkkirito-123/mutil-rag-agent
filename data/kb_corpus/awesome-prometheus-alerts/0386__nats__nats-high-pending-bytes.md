# Nats high pending bytes

> Group: **Message brokers**  
> Service: **Nats**  
> Exporter: `nats-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

NATS server has more than 100,000 pending bytes

## PromQL 查询

```promql
gnatsd_connz_pending_bytes > 100000
```

## 故障定位

- 触发该告警时, 检查 Nats 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / Nats
