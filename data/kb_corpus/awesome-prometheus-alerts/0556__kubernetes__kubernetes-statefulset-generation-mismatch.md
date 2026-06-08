# Kubernetes StatefulSet generation mismatch

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **critical**  
> Duration (for): `10m`

## 现象 / Description

StatefulSet {{ $labels.namespace }}/{{ $labels.statefulset }} has failed but has not been rolled back.

## PromQL 查询

```promql
kube_statefulset_status_observed_generation != kube_statefulset_metadata_generation
```

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
