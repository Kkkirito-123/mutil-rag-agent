# OpenTelemetry Collector exporter queue nearly full

> Group: **Observability**  
> Service: **OpenTelemetry Collector**  
> Exporter: `embedded-exporter`  
> Severity: **warning**

## 现象 / Description

OpenTelemetry Collector exporter {{ $labels.exporter }} queue is over 80% full

## PromQL 查询

```promql
(otelcol_exporter_queue_size / on(instance, job, exporter) otelcol_exporter_queue_capacity) > 0.8 and otelcol_exporter_queue_capacity > 0
```

## 故障定位

- 触发该告警时, 检查 OpenTelemetry Collector 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / OpenTelemetry Collector
