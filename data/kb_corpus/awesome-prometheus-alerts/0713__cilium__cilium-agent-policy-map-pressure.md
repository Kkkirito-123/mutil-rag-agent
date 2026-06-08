# Cilium agent policy map pressure

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Cilium agent {{ $labels.pod }} policy BPF map is above 90% utilization. New policies may fail to apply.

## PromQL 查询

```promql
sum(cilium_bpf_map_pressure{map_name=~"cilium_policy_.*"}) by (pod) > 0.9
```

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / Cilium
