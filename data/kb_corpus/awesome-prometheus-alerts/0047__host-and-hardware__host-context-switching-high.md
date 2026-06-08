# Host context switching high

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **warning**

## 现象 / Description

Context switching is growing on the node (twice the daily average during the last 15m)

## PromQL 查询

```promql
(rate(node_context_switches_total[15m])/count without(mode,cpu) (node_cpu_seconds_total{mode="idle"})) / (rate(node_context_switches_total[1d])/count without(mode,cpu) (node_cpu_seconds_total{mode="idle"})) > 2 and rate(node_context_switches_total[1d]) > 0
```

## 处理建议 / Comments

x2 context switches is an arbitrary number.
The alert threshold depends on the nature of the application.
Please read: https://github.com/samber/awesome-prometheus-alerts/issues/58

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
