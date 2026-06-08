# PVE cluster not quorate

> Group: **Basic resource monitoring**  
> Service: **Proxmox VE**  
> Exporter: `prometheus-pve-exporter`  
> Severity: **critical**

## 现象 / Description

Proxmox VE cluster has lost quorum.

## PromQL 查询

```promql
pve_cluster_info{quorate="0"} == 1
```

## 处理建议 / Comments

Loss of quorum means the cluster cannot make decisions about VM placement
and fencing. This requires immediate attention.

## 故障定位

- 触发该告警时, 检查 Proxmox VE 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Proxmox VE
