# PVE guest not backed up

> Group: **Basic resource monitoring**  
> Service: **Proxmox VE**  
> Exporter: `prometheus-pve-exporter`  
> Severity: **warning**

## 现象 / Description

{{ $value }} Proxmox VE guest(s) are not covered by any backup job.

## PromQL 查询

```promql
pve_not_backed_up_total > 0
```

## 故障定位

- 触发该告警时, 检查 Proxmox VE 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Proxmox VE
