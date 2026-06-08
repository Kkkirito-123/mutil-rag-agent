# OpenTelemetry Collector receiver refused log records

> Group: **Observability**  
> Service: **OpenTelemetry Collector**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

OpenTelemetry Collector is refusing {{ $value | humanize }}/s log records on {{ $labels.receiver }}.

## PromQL 查询

```promql
rate(otelcol_receiver_refused_log_records[5m]) > 0.05
```

## 处理建议 / Comments

Threshold of 0.05/s avoids firing on transient single-event spikes.

## 故障定位

- 触发该告警时, 检查 OpenTelemetry Collector 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / OpenTelemetry Collector
