# Prometheus target scrape duplicate

> Group: **Basic resource monitoring**  
> Service: **Prometheus self-monitoring**  
> Exporter: `embedded-exporter`  
> Severity: **warning**

## 现象 / Description

Prometheus has many samples rejected due to duplicate timestamps but different values ({{ $value }} samples)

## PromQL 查询

```promql
increase(prometheus_target_scrapes_sample_duplicate_timestamp_total[5m]) > 3
```

## 故障定位

- 触发该告警时, 检查 Prometheus self-monitoring 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Prometheus self-monitoring
