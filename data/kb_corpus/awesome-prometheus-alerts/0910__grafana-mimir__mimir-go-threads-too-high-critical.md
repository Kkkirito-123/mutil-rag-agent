# Mimir go threads too high critical

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `15m`

## 现象 / Description

Mimir {{ $labels.instance }} has {{ $value }} Go threads.

## PromQL 查询

```promql
go_threads{job=~".*(mimir|cortex).*"} > 8000
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
