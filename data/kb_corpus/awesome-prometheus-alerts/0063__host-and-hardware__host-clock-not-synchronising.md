# Host clock not synchronising

> Group: **Basic resource monitoring**  
> Service: **Host and hardware**  
> Exporter: `node-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Clock not synchronising. Ensure NTP is configured on this host.

## PromQL 查询

```promql
(min_over_time(node_timex_sync_status[1m]) == 0 and node_timex_maxerror_seconds >= 16)
```

## 故障定位

- 触发该告警时, 检查 Host and hardware 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Host and hardware
