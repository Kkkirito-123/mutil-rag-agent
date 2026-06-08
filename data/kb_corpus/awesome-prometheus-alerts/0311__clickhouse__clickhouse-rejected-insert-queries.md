# ClickHouse rejected insert queries

> Group: **Databases**  
> Service: **Clickhouse**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

INSERTs rejected due to too many active data parts. Reduce insert frequency.

## PromQL 查询

```promql
increase(ClickHouseProfileEvents_RejectedInserts[1m]) > 2
```

## 故障定位

- 触发该告警时, 检查 Clickhouse 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Clickhouse
