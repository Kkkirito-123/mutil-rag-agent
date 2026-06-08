# Host filesystem device error

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Error stat-ing the {{ $labels.mountpoint }} filesystem

## PromQL 查询

```promql
node_filesystem_device_error{fstype!~"^(fuse.*|tmpfs|cifs|nfs)"} == 1
```

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
