# Mimir ruler missed evaluations

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Mimir ruler {{ $labels.instance }} is missing {{ printf "%.2f" $value }}% of rule group evaluations.

## PromQL 查询

```promql
100 * sum by (instance, job) (rate(cortex_prometheus_rule_group_iterations_missed_total[5m])) / sum by (instance, job) (rate(cortex_prometheus_rule_group_iterations_total[5m])) > 1 and sum by (instance, job) (rate(cortex_prometheus_rule_group_iterations_total[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
