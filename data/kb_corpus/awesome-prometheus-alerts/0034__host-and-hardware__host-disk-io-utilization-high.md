# Host disk IO utilization high

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **warning**

## 现象 / Description

Disk utilization is high (> 80%)

## PromQL 查询

```promql
(rate(node_disk_io_time_seconds_total[5m]) > .80)
```

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
