# Cilium agent NAT table full

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Cilium agent {{ $labels.pod }} NAT table is full, causing masquerade failures. Increase NAT map size or investigate.

## PromQL 查询

```promql
sum(rate(cilium_drop_count_total{reason="No mapping for NAT masquerade"}[1m])) by (pod) > 0
```

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Network and security / Cilium
