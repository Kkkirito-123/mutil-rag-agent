# Host high CPU load

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

CPU load is > 80%

## PromQL 查询

```promql
1 - (avg without (cpu) (rate(node_cpu_seconds_total{mode="idle"}[5m]))) > .80
```

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
