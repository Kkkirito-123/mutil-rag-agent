# Process exporter high context switching

> Group: **Basic resource monitoring**  
> Service: **Process Exporter**  
> Exporter: `process-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Process group {{ $labels.groupname }} has a high rate of context switches ({{ $value }}/s). (instance {{ $labels.instance }})

## PromQL 查询

```promql
rate(namedprocess_namegroup_context_switches_total{ctxswitchtype="voluntary"}[5m]) > 50000
```

## 处理建议 / Comments

Filters to voluntary switches only — involuntary switches are normal under CPU contention. Threshold of 50000/s is a rough default. Adjust based on workload.

## 故障定位

- 触发该告警时, 检查 Process Exporter 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Process Exporter
