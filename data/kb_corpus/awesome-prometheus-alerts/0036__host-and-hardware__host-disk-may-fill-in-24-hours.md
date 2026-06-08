# Host disk may fill in 24 hours

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Filesystem will likely run out of space within the next 24 hours.

## PromQL 查询

```promql
predict_linear(node_filesystem_avail_bytes{fstype!~"^(fuse.*|tmpfs|cifs|nfs)"}[3h], 86400) <= 0 and node_filesystem_avail_bytes > 0
```

## 处理建议 / Comments

Please add ignored mountpoints in node_exporter parameters like
"--collector.filesystem.ignored-mount-points=^/(sys|proc|dev|run)($|/)".
Same rule using "node_filesystem_free_bytes" will fire when disk fills for non-root users.

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
