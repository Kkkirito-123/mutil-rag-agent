# Pulsar subscription high number of backlog entries

> Group: **Message brokers**  
> Service: **Pulsar**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `1h`

## 现象 / Description

The number of subscription backlog entries is over 5k

## PromQL 查询

```promql
sum(pulsar_subscription_back_log) by (subscription) > 5000
```

## 故障定位

- 触发该告警时, 检查 Pulsar 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / Pulsar
