# Process exporter high file descriptor usage

> Group: **Basic resource monitoring**  
> Service: **Process Exporter**  
> Exporter: `process-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Process group {{ $labels.groupname }} is using more than 80% of its file descriptor limit. (instance {{ $labels.instance }})

## PromQL 查询

```promql
namedprocess_namegroup_worst_fd_ratio > 0.8
```

## 故障定位

- 触发该告警时, 检查 Process Exporter 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Process Exporter
