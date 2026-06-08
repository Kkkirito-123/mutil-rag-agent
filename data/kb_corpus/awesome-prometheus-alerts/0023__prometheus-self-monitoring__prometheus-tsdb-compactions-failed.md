# Prometheus TSDB compactions failed

> Group: **Basic resource monitoring**  
> Service: **Prometheus self-monitoring**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Prometheus encountered {{ $value }} TSDB compactions failures

## PromQL 查询

```promql
increase(prometheus_tsdb_compactions_failed_total[1m]) > 0
```

## 故障定位

- 触发该告警时, 检查 Prometheus self-monitoring 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Prometheus self-monitoring
