# Outdated Snapshots

> Group: **Basic resource monitoring**  
> Service: **VMware**  
> Exporter: `pryorda-vmware-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Outdated snapshots on {{ $labels.instance }}: {{ $value | printf "%.0f"}} days

## PromQL 查询

```promql
(time() - vmware_vm_snapshot_timestamp_seconds) / (60 * 60 * 24) >= 3
```

## 故障定位

- 触发该告警时, 检查 VMware 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / VMware
