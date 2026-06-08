# ZFS offline pool

> Group: **Storage**  
> Service: **ZFS**  
> Exporter: `node-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

A ZFS zpool is in a unexpected state: {{ $labels.state }}.

## PromQL 查询

```promql
node_zfs_zpool_state{state!="online"} > 0
```

## 故障定位

- 触发该告警时, 检查 ZFS 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Storage / ZFS
