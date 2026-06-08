# Thanos Rule Queue Is Dropping Alerts

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-ruler`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Thanos Rule {{$labels.instance}} is failing to queue alerts ({{ $value | humanize }}/s).

## PromQL 查询

```promql
sum by (job, instance) (rate(thanos_alert_queue_alerts_dropped_total[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Thanos
