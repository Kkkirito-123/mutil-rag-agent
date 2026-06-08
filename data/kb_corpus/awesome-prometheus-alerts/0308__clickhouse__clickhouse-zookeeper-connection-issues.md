# ClickHouse ZooKeeper Connection Issues

> Group: **Databases**  
> Service: **Clickhouse**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `3m`

## 现象 / Description

ClickHouse is experiencing issues with ZooKeeper connections, which may affect cluster state and coordination.

## PromQL 查询

```promql
ClickHouseMetrics_ZooKeeperSession != 1
```

## 故障定位

- 触发该告警时, 检查 Clickhouse 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Clickhouse
