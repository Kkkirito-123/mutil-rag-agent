# Host inodes may fill in 24 hours

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Filesystem will likely run out of inodes within the next 24 hours at current write rate

## PromQL 查询

```promql
predict_linear(node_filesystem_files_free{fstype!~"^(fuse.*|tmpfs|cifs|nfs)"}[1h], 86400) <= 0 and node_filesystem_files_free > 0
```

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
