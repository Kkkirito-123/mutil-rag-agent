# Kubernetes Deployment generation mismatch

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **critical**  
> Duration (for): `10m`

## 现象 / Description

Deployment {{ $labels.namespace }}/{{ $labels.deployment }} has failed but has not been rolled back.

## PromQL 查询

```promql
kube_deployment_status_observed_generation != kube_deployment_metadata_generation
```

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
