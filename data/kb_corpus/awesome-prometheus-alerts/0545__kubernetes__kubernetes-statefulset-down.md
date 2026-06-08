# Kubernetes StatefulSet down

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

StatefulSet {{ $labels.namespace }}/{{ $labels.statefulset }} went down

## PromQL 查询

```promql
kube_statefulset_replicas != kube_statefulset_status_replicas_ready > 0
```

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
