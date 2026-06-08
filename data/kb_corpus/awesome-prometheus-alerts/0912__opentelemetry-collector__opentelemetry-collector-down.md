# OpenTelemetry Collector down

> Group: **Observability**  
> Service: **OpenTelemetry Collector**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

OpenTelemetry Collector instance has disappeared or is not being scraped

## PromQL 查询

```promql
up{job=~".*otel.*collector.*"} == 0
```

## 处理建议 / Comments

Adjust the job label regex to match the actual job name in your Prometheus scrape config.

## 故障定位

- 触发该告警时, 检查 OpenTelemetry Collector 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / OpenTelemetry Collector
