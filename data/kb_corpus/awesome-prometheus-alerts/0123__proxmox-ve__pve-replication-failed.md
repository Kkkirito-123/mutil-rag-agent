# PVE replication failed

> Group: **Basic resource monitoring**  
> Service: **Proxmox VE**  
> Exporter: `prometheus-pve-exporter`  
> Severity: **warning**

## 现象 / Description

Proxmox VE replication for {{ $labels.id }} has {{ $value }} failed sync(s).

## PromQL 查询

```promql
pve_replication_failed_syncs > 0
```

## 故障定位

- 触发该告警时, 检查 Proxmox VE 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Proxmox VE
