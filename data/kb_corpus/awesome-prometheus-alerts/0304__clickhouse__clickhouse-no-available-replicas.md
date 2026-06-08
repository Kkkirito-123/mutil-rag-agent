# ClickHouse No Available Replicas

> Group: **Databases**  
> Service: **Clickhouse**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

No available replicas in ClickHouse.

## PromQL 查询

```promql
ClickHouseErrorMetric_NO_AVAILABLE_REPLICA == 1
```

## 故障定位

- 触发该告警时, 检查 Clickhouse 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Clickhouse
