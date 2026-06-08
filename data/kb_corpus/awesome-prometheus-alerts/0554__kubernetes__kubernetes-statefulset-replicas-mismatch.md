# Kubernetes StatefulSet replicas mismatch

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

StatefulSet does not match the expected number of replicas.

## PromQL 查询

```promql
kube_statefulset_status_replicas_ready != kube_statefulset_status_replicas
```

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
