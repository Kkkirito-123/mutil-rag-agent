# ClickHouse Access Denied Errors

> Group: **Databases**  
> Service: **Clickhouse**  
> Exporter: `embedded-exporter`  
> Severity: **info**

## 现象 / Description

Access denied errors have been logged, which could indicate permission issues or unauthorized access attempts.

## PromQL 查询

```promql
increase(ClickHouseErrorMetric_RESOURCE_ACCESS_DENIED[5m]) > 3
```

## 故障定位

- 触发该告警时, 检查 Clickhouse 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Databases / Clickhouse
