# Host software RAID insufficient drives

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **critical**

## 现象 / Description

MD RAID array {{ $labels.device }} on {{ $labels.instance }} has insufficient drives remaining.

## PromQL 查询

```promql
((node_md_disks_required - ignoring(state) node_md_disks{state="active"}) > 0)
```

## 处理建议 / Comments

Uses ignoring(state) to handle additional labels on node_md_disks.

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
