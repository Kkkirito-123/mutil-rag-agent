# Host software RAID disk failure

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

MD RAID array {{ $labels.device }} on {{ $labels.instance }} needs attention.

## PromQL 查询

```promql
(node_md_disks{state="failed"} > 0)
```

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
