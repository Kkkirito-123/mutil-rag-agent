# Cilium Hubble lost events

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Cilium Hubble on {{ $labels.pod }} is losing flow events. Observability data may be incomplete.

## PromQL 查询

```promql
sum(rate(hubble_lost_events_total[5m])) by (pod) > 0.05
```

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / Cilium
