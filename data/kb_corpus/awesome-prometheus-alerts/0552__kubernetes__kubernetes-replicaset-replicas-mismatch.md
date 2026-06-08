# Kubernetes ReplicaSet replicas mismatch

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

ReplicaSet {{ $labels.namespace }}/{{ $labels.replicaset }} replicas mismatch

## PromQL 查询

```promql
kube_replicaset_spec_replicas != kube_replicaset_status_ready_replicas
```

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
