# PVE VM/CT down

> Group: **Basic resource monitoring**  
> Service: **Proxmox VE**  
> Exporter: `prometheus-pve-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Proxmox VE guest {{ $labels.id }} is not running.

## PromQL 查询

```promql
pve_up{id=~"(qemu|lxc)/.*"} == 0
```

## 处理建议 / Comments

This alert triggers for all VMs and containers that are not running.
You may want to filter by specific guests using the `id` label, or exclude
intentionally stopped guests with additional label matchers.

## 故障定位

- 触发该告警时, 检查 Proxmox VE 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Proxmox VE
