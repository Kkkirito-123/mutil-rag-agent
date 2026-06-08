# Host kernel version deviations

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **info**

## 现象 / Description

Kernel version for {{ $labels.instance }} has changed.

## PromQL 查询

```promql
changes(node_uname_info[1h]) > 0
```

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
