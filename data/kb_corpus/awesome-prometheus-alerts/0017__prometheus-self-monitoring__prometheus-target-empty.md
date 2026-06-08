# Prometheus target empty

> Group: **Basic resource monitoring**  
> Service: **Prometheus self-monitoring**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Prometheus has no target in service discovery

## PromQL 查询

```promql
prometheus_sd_discovered_targets == 0
```

## 故障定位

- 触发该告警时, 检查 Prometheus self-monitoring 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Prometheus self-monitoring
