# Process exporter high disk write IO

> Group: **Basic resource monitoring**  
> Service: **Process Exporter**  
> Exporter: `process-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Process group {{ $labels.groupname }} is performing {{ $value | humanize }}B/s of disk writes. (instance {{ $labels.instance }})

## PromQL 查询

```promql
rate(namedprocess_namegroup_write_bytes_total[5m]) > 100e+06
```

## 处理建议 / Comments

Threshold of 100MB/s is arbitrary. Adjust per group.

## 故障定位

- 触发该告警时, 检查 Process Exporter 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Process Exporter
