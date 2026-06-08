# ZFS pool unhealthy

> Group: **Storage**  
> Service: **ZFS**  
> Exporter: `zfs_exporter`  
> Severity: **critical**

## 现象 / Description

ZFS pool state is {{ $value }}. See comments for more information.

## PromQL 查询

```promql
zfs_pool_health > 0
```

## 处理建议 / Comments

0: ONLINE
1: DEGRADED
2: FAULTED
3: OFFLINE
4: UNAVAIL
5: REMOVED
6: SUSPENDED

## 故障定位

- 触发该告警时, 检查 ZFS 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Storage / ZFS
