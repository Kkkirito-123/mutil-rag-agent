# Kubernetes StatefulSet update not rolled out

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

StatefulSet {{ $labels.namespace }}/{{ $labels.statefulset }} update has not been rolled out.

## PromQL 查询

```promql
max without (revision) (kube_statefulset_status_current_revision unless kube_statefulset_status_update_revision) * (kube_statefulset_replicas != kube_statefulset_status_replicas_updated)
```

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
