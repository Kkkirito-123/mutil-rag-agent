# Prometheus target missing with warmup time

> Group: **Basic resource monitoring**  
> Service: **Prometheus self-monitoring**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Allow a job time to start up (10 minutes) before alerting that it's down.

## PromQL 查询

```promql
sum by (instance, job) ((up == 0) * on (instance) group_left(__name__) (node_time_seconds - node_boot_time_seconds > 600))
```

## 故障定位

- 触发该告警时, 检查 Prometheus self-monitoring 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Prometheus self-monitoring
