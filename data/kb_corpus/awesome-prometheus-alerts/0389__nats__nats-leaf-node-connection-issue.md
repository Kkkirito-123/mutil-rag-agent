# Nats leaf node connection issue

> Group: **Message brokers**  
> Service: **Nats**  
> Exporter: `nats-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

No leaf node connections on {{ $labels.instance }}

## PromQL 查询

```promql
gnatsd_varz_leafnodes == 0
```

## 处理建议 / Comments

Only enable this alert if your deployment requires leaf node connections.
This will fire spuriously if leaf nodes are not configured.

## 故障定位

- 触发该告警时, 检查 Nats 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Message brokers / Nats
