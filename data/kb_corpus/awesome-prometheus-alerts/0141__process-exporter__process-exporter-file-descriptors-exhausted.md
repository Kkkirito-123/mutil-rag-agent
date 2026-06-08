# Process exporter file descriptors exhausted

> Group: **Basic resource monitoring**  
> Service: **Process Exporter**  
> Exporter: `process-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Process group {{ $labels.groupname }} has nearly exhausted its file descriptor limit. (instance {{ $labels.instance }})

## PromQL 查询

```promql
namedprocess_namegroup_worst_fd_ratio > 0.95
```

## 故障定位

- 触发该告警时, 检查 Process Exporter 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Process Exporter
