# PVE storage almost full

> Group: **Basic resource monitoring**  
> Service: **Proxmox VE**  
> Exporter: `prometheus-pve-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Proxmox VE storage {{ $labels.id }} is above 95% used. Current value: {{ $value | printf "%.2f" }}%

## PromQL 查询

```promql
pve_disk_usage_bytes{id=~"storage/.*"} / pve_disk_size_bytes{id=~"storage/.*"} * 100 > 95 and pve_disk_size_bytes{id=~"storage/.*"} > 0
```

## 故障定位

- 触发该告警时, 检查 Proxmox VE 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Proxmox VE
