# Host out of memory

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Node memory is filling up (< 10% left)

## PromQL 查询

```promql
(node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes < .10)
```

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
