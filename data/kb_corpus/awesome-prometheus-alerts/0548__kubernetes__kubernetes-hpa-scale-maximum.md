# Kubernetes HPA scale maximum

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **info**  
> Duration (for): `2m`

## 现象 / Description

HPA {{ $labels.namespace }}/{{ $labels.horizontalpodautoscaler }} has hit maximum number of desired pods

## PromQL 查询

```promql
(kube_horizontalpodautoscaler_status_desired_replicas >= kube_horizontalpodautoscaler_spec_max_replicas) and (kube_horizontalpodautoscaler_spec_max_replicas > 1) and (kube_horizontalpodautoscaler_spec_min_replicas != kube_horizontalpodautoscaler_spec_max_replicas)
```

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
