# Container high throttle rate

> Group: **Basic resource monitoring**  
> Service: **Docker containers**  
> Exporter: `google-cadvisor`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Container is being throttled ({{ $value | humanizePercentage }})

## PromQL 查询

```promql
sum(rate(container_cpu_cfs_throttled_periods_total{container!=""}[5m])) by (container, pod, namespace) / sum(rate(container_cpu_cfs_periods_total[5m])) by (container, pod, namespace) > ( 25 / 100 ) and sum(rate(container_cpu_cfs_periods_total[5m])) by (container, pod, namespace) > 0
```

## 故障定位

- 触发该告警时, 检查 Docker containers 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Docker containers
