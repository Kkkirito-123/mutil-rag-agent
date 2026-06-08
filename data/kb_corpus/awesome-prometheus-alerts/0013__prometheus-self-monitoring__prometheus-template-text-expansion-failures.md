# Prometheus template text expansion failures

> Group: **Basic resource monitoring**  
> Service: **Prometheus self-monitoring**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Prometheus encountered {{ $value }} template text expansion failures

## PromQL 查询

```promql
increase(prometheus_template_text_expansion_failures_total[3m]) > 0
```

## 故障定位

- 触发该告警时, 检查 Prometheus self-monitoring 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Prometheus self-monitoring
