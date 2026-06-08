# ZFS pool out of space

> Group: **Storage**  
> Service: **ZFS**  
> Exporter: `zfs_exporter`  
> Severity: **warning**

## 现象 / Description

ZFS pool {{ $labels.pool }} is almost full (< 10% left).

## PromQL 查询

```promql
zfs_pool_free_bytes * 100 / zfs_pool_size_bytes < 10 and zfs_pool_readonly == 0 and zfs_pool_size_bytes > 0
```

## 故障定位

- 触发该告警时, 检查 ZFS 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Storage / ZFS
