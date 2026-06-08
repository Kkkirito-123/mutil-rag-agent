# Nats slow consumers

> Group: **Message brokers**  
> Service: **Nats**  
> Exporter: `nats-exporter`  
> Severity: **critical**  
> Duration (for): `3m`

## 现象 / Description

There are slow consumers in NATS for {{ $labels.instance }}

## PromQL 查询

```promql
gnatsd_varz_slow_consumers > 0
```

## 故障定位

- 触发该告警时, 检查 Nats 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Message brokers / Nats
