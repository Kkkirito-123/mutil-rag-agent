# Cilium agent high drop rate

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Cilium agent {{ $labels.pod }} is dropping packets for reason {{ $labels.reason }}. This indicates infrastructure issues.

## PromQL 查询

```promql
sum(rate(cilium_drop_count_total{reason!~"Policy denied"}[5m])) by (pod, reason) > 0.05
```

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / Cilium
