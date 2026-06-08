# Pulsar subscription very high number of backlog entries

> Group: **Message brokers**  
> Service: **Pulsar**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `1h`

## 现象 / Description

The number of subscription backlog entries is over 100k

## PromQL 查询

```promql
sum(pulsar_subscription_back_log) by (subscription) > 100000
```

## 故障定位

- 触发该告警时, 检查 Pulsar 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Message brokers / Pulsar
