# OpenTelemetry Collector processor refused spans

> Group: **Observability**  
> Service: **OpenTelemetry Collector**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

OpenTelemetry Collector processor {{ $labels.processor }} is refusing spans ({{ $value | humanize }}/s), likely due to backpressure.

## PromQL 查询

```promql
rate(otelcol_processor_refused_spans[5m]) > 0.05
```

## 处理建议 / Comments

Threshold of 0.05/s avoids firing on transient single-event spikes.
These processor metrics are deprecated since collector v0.110.0.

## 故障定位

- 触发该告警时, 检查 OpenTelemetry Collector 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / OpenTelemetry Collector
