# Host CPU is underutilized

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **info**  
> Duration (for): `1w`

## 现象 / Description

CPU load has been < 20% for 1 week. Consider reducing the number of CPUs.

## PromQL 查询

```promql
(min without (cpu) (rate(node_cpu_seconds_total{mode="idle"}[1h]))) > 0.8
```

## 处理建议 / Comments

You may want to increase the alert manager 'repeat_interval' for this type of alert to daily or weekly

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
