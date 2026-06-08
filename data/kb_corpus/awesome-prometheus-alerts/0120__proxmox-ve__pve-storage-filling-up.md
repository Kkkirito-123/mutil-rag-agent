# PVE storage filling up

> Group: **Basic resource monitoring**  
> Service: **Proxmox VE**  
> Exporter: `prometheus-pve-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Proxmox VE storage {{ $labels.id }} is above 80% used. Current value: {{ $value | printf "%.2f" }}%

## PromQL 查询

```promql
pve_disk_usage_bytes{id=~"storage/.*"} / pve_disk_size_bytes{id=~"storage/.*"} * 100 > 80 and pve_disk_size_bytes{id=~"storage/.*"} > 0
```

## 故障定位

- 触发该告警时, 检查 Proxmox VE 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Proxmox VE
