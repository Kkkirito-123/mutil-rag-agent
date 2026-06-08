# ZFS collector failed

> Group: **Storage**  
> Service: **ZFS**  
> Exporter: `zfs_exporter`  
> Severity: **warning**

## 现象 / Description

ZFS collector for {{ $labels.instance }} has failed to collect information

## PromQL 查询

```promql
zfs_scrape_collector_success != 1
```

## 故障定位

- 触发该告警时, 检查 ZFS 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Storage / ZFS
