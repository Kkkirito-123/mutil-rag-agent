# MongoDB number cursors open (Percona)

> Group: **Databases**  
> Service: **MongoDB**  
> Exporter: `percona-mongodb-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Too many cursors opened by MongoDB for clients (> 10k)

## PromQL 查询

```promql
mongodb_ss_metrics_cursor_open{csr_type="total"} > 10 * 1000
```

## 故障定位

- 触发该告警时, 检查 MongoDB 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / MongoDB
