# OpenTelemetry Collector high memory usage

> Group: **Observability**  
> Service: **OpenTelemetry Collector**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

OpenTelemetry Collector memory usage is above 90%

## PromQL 查询

```promql
(otelcol_process_runtime_heap_alloc_bytes / on(instance, job) otelcol_process_runtime_total_sys_memory_bytes) > 0.9
```

## 故障定位

- 触发该告警时, 检查 OpenTelemetry Collector 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / OpenTelemetry Collector
