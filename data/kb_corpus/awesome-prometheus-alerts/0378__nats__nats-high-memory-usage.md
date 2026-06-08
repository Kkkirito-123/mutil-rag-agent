# Nats high memory usage

> Group: **Message brokers**  
> Service: **Nats**  
> Exporter: `nats-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

NATS server memory usage is above 200MB for {{ $labels.instance }}

## PromQL 查询

```promql
gnatsd_varz_mem > 200 * 1024 * 1024
```

## 故障定位

- 触发该告警时, 检查 Nats 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / Nats
