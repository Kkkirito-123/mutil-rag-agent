# Prometheus notifications backlog

> Group: **Basic resource monitoring**  
> Service: **Prometheus self-monitoring**  
> Exporter: `embedded-exporter`  
> Severity: **warning**

## 现象 / Description

The Prometheus notification queue has not been empty for 10 minutes

## PromQL 查询

```promql
min_over_time(prometheus_notifications_queue_length[10m]) > 0
```

## 故障定位

- 触发该告警时, 检查 Prometheus self-monitoring 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Prometheus self-monitoring
