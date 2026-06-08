# Host CPU steal noisy neighbor

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **warning**

## 现象 / Description

CPU steal is > 10%. A noisy neighbor is killing VM performances or a spot instance may be out of credit.

## PromQL 查询

```promql
avg without (cpu) (rate(node_cpu_seconds_total{mode="steal"}[5m])) * 100 > 10
```

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
