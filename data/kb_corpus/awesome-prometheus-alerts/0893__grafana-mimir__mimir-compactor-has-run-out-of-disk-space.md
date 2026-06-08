# Mimir compactor has run out of disk space

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Mimir compactor {{ $labels.instance }} has run out of disk space.

## PromQL 查询

```promql
delta(cortex_compactor_disk_out_of_space_errors_total[24h]) >= 1
```

## 处理建议 / Comments

cortex_compactor_disk_out_of_space_errors_total is declared as gauge by Mimir despite the _total suffix, so delta() is used instead of increase().

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
