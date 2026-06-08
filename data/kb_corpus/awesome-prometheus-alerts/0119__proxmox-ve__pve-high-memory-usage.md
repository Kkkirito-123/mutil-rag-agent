# PVE high memory usage

> Group: **Basic resource monitoring**  
> Service: **Proxmox VE**  
> Exporter: `prometheus-pve-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Proxmox VE memory usage is above 90% on {{ $labels.id }}. Current value: {{ $value | printf "%.2f" }}%

## PromQL 查询

```promql
pve_memory_usage_bytes / pve_memory_size_bytes * 100 > 90 and pve_memory_size_bytes > 0
```

## 故障定位

- 触发该告警时, 检查 Proxmox VE 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Proxmox VE
