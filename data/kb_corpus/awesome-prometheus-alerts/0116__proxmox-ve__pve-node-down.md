# PVE node down

> Group: **Basic resource monitoring**  
> Service: **Proxmox VE**  
> Exporter: `prometheus-pve-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Proxmox VE node {{ $labels.id }} is down.

## PromQL 查询

```promql
pve_up{id=~"node/.*"} == 0
```

## 故障定位

- 触发该告警时, 检查 Proxmox VE 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Proxmox VE
