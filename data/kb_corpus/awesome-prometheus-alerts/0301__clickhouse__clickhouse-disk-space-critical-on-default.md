# ClickHouse Disk Space Critical on Default

> Group: **Databases**  
> Service: **Clickhouse**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Disk space on default disk is critically low, below 10%.

## PromQL 查询

```promql
ClickHouseAsyncMetrics_DiskAvailable_default / (ClickHouseAsyncMetrics_DiskAvailable_default + ClickHouseAsyncMetrics_DiskUsed_default) * 100 < 10 and (ClickHouseAsyncMetrics_DiskAvailable_default + ClickHouseAsyncMetrics_DiskUsed_default) > 0
```

## 故障定位

- 触发该告警时, 检查 Clickhouse 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Clickhouse
