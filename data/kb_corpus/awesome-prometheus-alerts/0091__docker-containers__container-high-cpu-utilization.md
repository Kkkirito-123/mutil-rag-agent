# Container High CPU utilization

> Group: **Basic resource monitoring**  
> Service: **Docker containers**  
> Exporter: `google-cadvisor`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Container CPU utilization is above 80% (current: {{ $value | printf "%.2f" }}%)

## PromQL 查询

```promql
(sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (pod, container) / sum(container_spec_cpu_quota{container!=""}/container_spec_cpu_period{container!=""}) by (pod, container) * 100) > 80 and sum(container_spec_cpu_quota{container!=""}/container_spec_cpu_period{container!=""}) by (pod, container) > 0
```

## 处理建议 / Comments

Only fires for containers with explicit CPU limits. Containers without limits have cpu_quota=0, which is filtered out by the guard.

## 故障定位

- 触发该告警时, 检查 Docker containers 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Docker containers
