# Cilium agent BPF map pressure

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Cilium agent {{ $labels.pod }} eBPF map {{ $labels.map_name }} is above 90% utilization. Map may become full.

## PromQL 查询

```promql
cilium_bpf_map_pressure{} > 0.9
```

## 处理建议 / Comments

Map pressure is a ratio from 0 to 1. At 1.0, the map is full and new entries will be dropped.

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / Cilium
