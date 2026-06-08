# Prometheus large scrape

> Group: **Basic resource monitoring**  
> Service: **Prometheus self-monitoring**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Prometheus has many scrapes that exceed the sample limit ({{ $value }} scrapes)

## PromQL 查询

```promql
increase(prometheus_target_scrapes_exceeded_sample_limit_total[10m]) > 10
```

## 故障定位

- 触发该告警时, 检查 Prometheus self-monitoring 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Prometheus self-monitoring
