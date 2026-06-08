# Prometheus rule evaluation slow

> Group: **Basic resource monitoring**  
> Service: **Prometheus self-monitoring**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Prometheus rule evaluation took more time than the scheduled interval. It indicates a slower storage backend access or too complex query.

## PromQL 查询

```promql
prometheus_rule_group_last_duration_seconds > prometheus_rule_group_interval_seconds
```

## 故障定位

- 触发该告警时, 检查 Prometheus self-monitoring 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Prometheus self-monitoring
