# Mimir inconsistent runtime config

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `1h`

## 现象 / Description

An inconsistent runtime config file is used across Mimir instances.

## PromQL 查询

```promql
count(count by (job, sha256) (cortex_runtime_config_hash)) without(sha256) > 1
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
