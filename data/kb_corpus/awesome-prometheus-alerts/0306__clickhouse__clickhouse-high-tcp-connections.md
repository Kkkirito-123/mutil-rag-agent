# ClickHouse High TCP Connections

> Group: **Databases**  
> Service: **Clickhouse**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

High number of TCP connections, indicating heavy client or inter-cluster communication.

## PromQL 查询

```promql
ClickHouseMetrics_TCPConnection > 400
```

## 处理建议 / Comments

Please replace the threshold with an appropriate value

## 故障定位

- 触发该告警时, 检查 Clickhouse 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Clickhouse
