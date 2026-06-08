# ClickHouse Interserver Connection Issues

> Group: **Databases**  
> Service: **Clickhouse**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

High number of interserver connections may indicate replication or distributed query handling issues.

## PromQL 查询

```promql
ClickHouseMetrics_InterserverConnection > 50
```

## 处理建议 / Comments

Adjust the threshold based on your cluster size and expected replication traffic.

## 故障定位

- 触发该告警时, 检查 Clickhouse 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Clickhouse
