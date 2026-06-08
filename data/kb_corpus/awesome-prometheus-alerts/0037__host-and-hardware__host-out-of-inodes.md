# Host out of inodes

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Disk is almost running out of available inodes (< 10% left)

## PromQL 查询

```promql
(node_filesystem_files_free / node_filesystem_files < .10 and ON (instance, device, mountpoint) node_filesystem_readonly == 0) and node_filesystem_files > 0
```

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
