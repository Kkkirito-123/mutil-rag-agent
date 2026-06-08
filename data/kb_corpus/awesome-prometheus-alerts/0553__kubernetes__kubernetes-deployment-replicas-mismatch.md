# Kubernetes Deployment replicas mismatch

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

Deployment {{ $labels.namespace }}/{{ $labels.deployment }} replicas mismatch

## PromQL 查询

```promql
kube_deployment_spec_replicas != kube_deployment_status_replicas_available
```

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
