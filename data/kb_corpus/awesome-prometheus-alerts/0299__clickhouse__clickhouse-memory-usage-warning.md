# ClickHouse Memory Usage Warning

> Group: **Databases**  
> Service: **Clickhouse**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Memory usage is over 80%.

## PromQL 查询

```promql
ClickHouseAsyncMetrics_CGroupMemoryUsed / ClickHouseAsyncMetrics_CGroupMemoryTotal * 100 > 80 and ClickHouseAsyncMetrics_CGroupMemoryTotal > 0
```

## 故障定位

- 触发该告警时, 检查 Clickhouse 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Clickhouse
