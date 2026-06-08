# Container Low CPU utilization

> Group: **Basic resource monitoring**  
> Service: **Docker containers**  
> Exporter: `google-cadvisor`  
> Severity: **info**  
> Duration (for): `7d`

## 现象 / Description

Container CPU utilization is under 20% for 1 week. Consider reducing the allocated CPU. (current: {{ $value | printf "%.2f" }}%)

## PromQL 查询

```promql
(sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (pod, container) / sum(container_spec_cpu_quota{container!=""}/container_spec_cpu_period{container!=""}) by (pod, container) * 100) < 20 and sum(container_spec_cpu_quota{container!=""}/container_spec_cpu_period{container!=""}) by (pod, container) > 0
```

## 故障定位

- 触发该告警时, 检查 Docker containers 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Docker containers
