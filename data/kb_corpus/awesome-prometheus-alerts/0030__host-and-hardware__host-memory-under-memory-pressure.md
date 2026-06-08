# Host memory under memory pressure

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **warning**

## 现象 / Description

The node is under heavy memory pressure. High rate of major page faults ({{ $value }}/s).

## PromQL 查询

```promql
(deriv(node_vmstat_pgmajfault[5m]) > 1000)
```

## 处理建议 / Comments

node_vmstat_pgmajfault is exposed as untyped/gauge by node_exporter (from /proc/vmstat), so deriv() is used instead of rate().

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
