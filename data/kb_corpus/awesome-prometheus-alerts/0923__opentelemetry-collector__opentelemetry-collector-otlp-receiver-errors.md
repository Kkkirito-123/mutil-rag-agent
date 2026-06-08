# OpenTelemetry Collector OTLP receiver errors

> Group: **Observability**  
> Service: **OpenTelemetry Collector**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

OpenTelemetry Collector OTLP receiver is completely failing - all spans are being refused

## PromQL 查询

```promql
rate(otelcol_receiver_accepted_spans{receiver=~"otlp"}[5m]) == 0 and rate(otelcol_receiver_refused_spans{receiver=~"otlp"}[5m]) > 0
```

## 故障定位

- 触发该告警时, 检查 OpenTelemetry Collector 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / OpenTelemetry Collector
