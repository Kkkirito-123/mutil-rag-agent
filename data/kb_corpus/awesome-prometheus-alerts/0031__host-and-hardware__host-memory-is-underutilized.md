# Host Memory is underutilized

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **info**

## 现象 / Description

Node memory usage is < 20% for 1 week. Consider reducing memory space. (instance {{ $labels.instance }})

## PromQL 查询

```promql
min_over_time(node_memory_MemFree_bytes[1w]) > node_memory_MemTotal_bytes * .8
```

## 处理建议 / Comments

You may want to increase the alert manager 'repeat_interval' for this type of alert to daily or weekly

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
