# Nats high routes count

> Group: **Message brokers**  
> Service: **Nats**  
> Exporter: `nats-exporter`  
> Severity: **warning**  
> Duration (for): `3m`

## 现象 / Description

High number of NATS routes ({{ $value }}) for {{ $labels.instance }}

## PromQL 查询

```promql
gnatsd_varz_routes > 10
```

## 故障定位

- 触发该告警时, 检查 Nats 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / Nats
