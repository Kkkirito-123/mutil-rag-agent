# Mimir ruler too many failed pushes

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Mimir ruler {{ $labels.instance }} is failing to push {{ printf "%.2f" $value }}% of write requests.

## PromQL 查询

```promql
100 * sum by (instance, job) (rate(cortex_ruler_write_requests_failed_total[5m])) / sum by (instance, job) (rate(cortex_ruler_write_requests_total[5m])) > 1 and sum by (instance, job) (rate(cortex_ruler_write_requests_total[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
