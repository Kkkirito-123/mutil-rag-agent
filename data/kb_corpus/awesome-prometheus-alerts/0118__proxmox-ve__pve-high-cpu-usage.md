# PVE high CPU usage

> Group: **Basic resource monitoring**  
> Service: **Proxmox VE**  
> Exporter: `prometheus-pve-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Proxmox VE CPU usage is above 90% on {{ $labels.id }}. Current value: {{ $value | printf "%.2f" }}%

## PromQL 查询

```promql
pve_cpu_usage_ratio * 100 > 90
```

## 故障定位

- 触发该告警时, 检查 Proxmox VE 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Proxmox VE
