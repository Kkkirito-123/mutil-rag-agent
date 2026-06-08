# Host OOM kill detected

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **warning**

## 现象 / Description

OOM kill detected

## PromQL 查询

```promql
(delta(node_vmstat_oom_kill[30m]) > 0)
```

## 处理建议 / Comments

When a machine runs out of memory, the node exporter can become unresponsive for several minutes. Even if the system takes 15–20 minutes to recover, the alert should still trigger.

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
