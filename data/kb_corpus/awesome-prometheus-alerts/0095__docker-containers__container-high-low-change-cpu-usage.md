# Container high low change CPU usage

> Group: **Basic resource monitoring**  
> Service: **Docker containers**  
> Exporter: `google-cadvisor`  
> Severity: **info**

## 现象 / Description

This alert rule monitors the absolute change in CPU usage within a time window and triggers an alert when the change exceeds 25%.

## PromQL 查询

```promql
(abs((sum by (instance, name) (rate(container_cpu_usage_seconds_total{name!=""}[1m])) * 100) - (sum by (instance, name) (rate(container_cpu_usage_seconds_total{name!=""}[1m] offset 1m)) * 100)) or abs((sum by (instance, name) (rate(container_cpu_usage_seconds_total{name!=""}[1m])) * 100) - (sum by (instance, name) (rate(container_cpu_usage_seconds_total{name!=""}[5m] offset 1m)) * 100))) > 25
```

## 故障定位

- 触发该告警时, 检查 Docker containers 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Docker containers
