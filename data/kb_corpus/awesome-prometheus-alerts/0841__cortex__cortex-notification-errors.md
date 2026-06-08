# Cortex notification errors

> Group: **Observability**  
> Service: **Cortex**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Cortex is failing when sending alert notifications (instance {{ $labels.instance }}, {{ $value | humanize }}/s).

## PromQL 查询

```promql
rate(cortex_prometheus_notifications_errors_total[5m]) > 0.05
```

## 处理建议 / Comments

Threshold of 0.05/s avoids firing on transient single-event spikes.

## 故障定位

- 触发该告警时, 检查 Cortex 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Cortex
