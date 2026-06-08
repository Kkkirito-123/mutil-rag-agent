# Grafana Alloy service down

> Group: **Observability**  
> Service: **Grafana Alloy**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Alloy on instance {{ $labels.instance }} is not responding or has stopped running.

## PromQL 查询

```promql
count by (instance) (alloy_build_info offset 2h) unless count by (instance) (alloy_build_info)
```

## 故障定位

- 触发该告警时, 检查 Grafana Alloy 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Alloy
