# Pulsar read only bookies

> Group: **Message brokers**  
> Service: **Pulsar**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Observing Readonly Bookies

## PromQL 查询

```promql
count(bookie_SERVER_STATUS{} == 0) by (pod)
```

## 故障定位

- 触发该告警时, 检查 Pulsar 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Message brokers / Pulsar
