# MongoDB cursors timeouts (DCU)

> Group: **Databases**  
> Service: **MongoDB**  
> Exporter: `dcu-mongodb-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Too many cursors are timing out ({{ $value }} in the last minute)

## PromQL 查询

```promql
increase(mongodb_metrics_cursor_timed_out_total[1m]) > 100
```

## 故障定位

- 触发该告警时, 检查 MongoDB 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / MongoDB
