# Process exporter high memory usage

> Group: **Basic resource monitoring**  
> Service: **Process Exporter**  
> Exporter: `process-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Process group {{ $labels.groupname }} is using {{ $value | humanize }}B of resident memory. (instance {{ $labels.instance }})

## PromQL 查询

```promql
namedprocess_namegroup_memory_bytes{memtype="resident"} > 4e+09
```

## 处理建议 / Comments

Threshold of 4GB is arbitrary and depends on the process being monitored. Adjust per group.

## 故障定位

- 触发该告警时, 检查 Process Exporter 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Process Exporter
