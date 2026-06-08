# Cilium agent unreachable health endpoints

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

Cilium agent {{ $labels.pod }} cannot reach {{ $value }} health endpoint(s). Node-to-node health probes are failing.

## PromQL 查询

```promql
sum(cilium_unreachable_health_endpoints{}) by (pod) > 0
```

## 处理建议 / Comments

Metric name depends on Cilium version. Use cilium_unreachable_health_endpoints (older) or cilium_node_connectivity_status (1.14+).

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / Cilium
