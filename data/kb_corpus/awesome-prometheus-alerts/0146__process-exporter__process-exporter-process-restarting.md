# Process exporter process restarting

> Group: **Basic resource monitoring**  
> Service: **Process Exporter**  
> Exporter: `process-exporter`  
> Severity: **info**

## 现象 / Description

Process group {{ $labels.groupname }} has restarted (oldest process start time changed). (instance {{ $labels.instance }})

## PromQL 查询

```promql
changes(namedprocess_namegroup_oldest_start_time_seconds[5m]) > 0 and namedprocess_namegroup_num_procs > 0
```

## 处理建议 / Comments

Detects restarts by watching for changes in the oldest process start time within the group.

## 故障定位

- 触发该告警时, 检查 Process Exporter 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Process Exporter
