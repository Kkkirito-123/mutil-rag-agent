# Cilium agent map operation failures

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Cilium agent {{ $labels.pod }} has eBPF map operation failures on {{ $labels.map_name }}. Datapath may be degraded.

## PromQL 查询

```promql
sum(rate(cilium_bpf_map_ops_total{outcome="fail"}[5m])) by (map_name, pod) > 0.05
```

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / Cilium
