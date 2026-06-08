# OpenTelemetry Collector exporter failed metric points

> Group: **Observability**  
> Service: **OpenTelemetry Collector**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

OpenTelemetry Collector failing to send {{ $value | humanize }}/s metric points via {{ $labels.exporter }}.

## PromQL 查询

```promql
rate(otelcol_exporter_send_failed_metric_points[5m]) > 0.05
```

## 处理建议 / Comments

Threshold of 0.05/s avoids firing on transient single-event spikes.

## 故障定位

- 触发该告警时, 检查 OpenTelemetry Collector 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / OpenTelemetry Collector
