# Prometheus too many restarts

> Group: **Basic resource monitoring**  
> Service: **Prometheus self-monitoring**  
> Exporter: `embedded-exporter`  
> Severity: **warning**

## 现象 / Description

Prometheus has restarted more than twice in the last 15 minutes. It might be crashlooping.

## PromQL 查询

```promql
changes(process_start_time_seconds{job=~"prometheus|pushgateway|alertmanager"}[15m]) > 2
```

## 故障定位

- 触发该告警时, 检查 Prometheus self-monitoring 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Prometheus self-monitoring
