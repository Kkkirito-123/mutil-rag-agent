# Process exporter high CPU usage

> Group: **Basic resource monitoring**  
> Service: **Process Exporter**  
> Exporter: `process-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Process group {{ $labels.groupname }} is using {{ $value }}% CPU (core-equivalent). (instance {{ $labels.instance }})

## PromQL 查询

```promql
rate(namedprocess_namegroup_cpu_seconds_total[5m]) * 100 > 80
```

## 处理建议 / Comments

Value is core-equivalent %: 100% = 1 full core, 200% = 2 cores, etc. Threshold of 80% is per-core. Adjust based on expected workload.

## 故障定位

- 触发该告警时, 检查 Process Exporter 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Process Exporter
