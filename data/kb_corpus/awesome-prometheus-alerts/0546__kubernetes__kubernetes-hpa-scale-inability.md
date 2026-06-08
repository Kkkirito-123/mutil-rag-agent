# Kubernetes HPA scale inability

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

HPA {{ $labels.namespace }}/{{ $labels.horizontalpodautoscaler }} is unable to scale

## PromQL 查询

```promql
(kube_horizontalpodautoscaler_spec_max_replicas - kube_horizontalpodautoscaler_status_desired_replicas) * on (horizontalpodautoscaler,namespace) (kube_horizontalpodautoscaler_status_condition{condition="ScalingLimited", status="true"} == 1) == 0
```

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
