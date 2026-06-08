# High Number of Snapshots

> Group: **Basic resource monitoring**  
> Service: **VMware**  
> Exporter: `pryorda-vmware-exporter`  
> Severity: **warning**  
> Duration (for): `30m`

## 现象 / Description

High snapshots number on {{ $labels.instance }}: {{ $value }}

## PromQL 查询

```promql
vmware_vm_snapshots > 3
```

## 故障定位

- 触发该告警时, 检查 VMware 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / VMware
