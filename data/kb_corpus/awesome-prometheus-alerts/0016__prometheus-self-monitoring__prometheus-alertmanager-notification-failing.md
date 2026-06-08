# Prometheus AlertManager notification failing

> Group: **Basic resource monitoring**  
> Service: **Prometheus self-monitoring**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Alertmanager is failing sending notifications ({{ $value }} notifications/s)

## PromQL 查询

```promql
rate(alertmanager_notifications_failed_total[3m]) > 0.05
```

## 故障定位

- 触发该告警时, 检查 Prometheus self-monitoring 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Prometheus self-monitoring
