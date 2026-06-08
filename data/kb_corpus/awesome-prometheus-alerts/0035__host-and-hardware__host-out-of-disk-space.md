# Host out of disk space

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Disk is almost full (< 10% left)

## PromQL 查询

```promql
(node_filesystem_avail_bytes{fstype!~"^(fuse.*|tmpfs|cifs|nfs)"} / node_filesystem_size_bytes < .10 and on (instance, device, mountpoint) node_filesystem_readonly == 0)
```

## 处理建议 / Comments

Please add ignored mountpoints in node_exporter parameters like
"--collector.filesystem.ignored-mount-points=^/(sys|proc|dev|run)($|/)".
Same rule using "node_filesystem_free_bytes" will fire when disk fills for non-root users.

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
