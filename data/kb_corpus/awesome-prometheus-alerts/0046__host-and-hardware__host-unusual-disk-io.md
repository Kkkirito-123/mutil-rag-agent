# Host unusual disk IO

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Disk usage >80%. Check storage for issues or increase IOPS capabilities.

## PromQL 查询

```promql
rate(node_disk_io_time_seconds_total[5m]) > 0.8
```

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
