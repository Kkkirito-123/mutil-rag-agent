# ClickHouse zookeeper hardware exception

> Group: **Databases**  
> Service: **Clickhouse**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Zookeeper hardware exception: network issues communicating with ZooKeeper

## PromQL 查询

```promql
increase(ClickHouseProfileEvents_ZooKeeperHardwareExceptions[1m]) > 0
```

## 故障定位

- 触发该告警时, 检查 Clickhouse 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Clickhouse
