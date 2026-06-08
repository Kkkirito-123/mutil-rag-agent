# Mimir distributor inflight requests high

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Mimir distributor {{ $labels.instance }} is using {{ printf "%.0f" $value }}% of its inflight push requests limit.

## PromQL 查询

```promql
(cortex_distributor_inflight_push_requests / ignoring(limit) cortex_distributor_instance_limits{limit="max_inflight_push_requests"} * 100 > 80) and cortex_distributor_instance_limits{limit="max_inflight_push_requests"} > 0
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
