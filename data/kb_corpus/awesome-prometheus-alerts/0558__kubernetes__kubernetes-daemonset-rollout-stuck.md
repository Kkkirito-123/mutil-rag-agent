# Kubernetes DaemonSet rollout stuck

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

Some Pods of DaemonSet {{ $labels.namespace }}/{{ $labels.daemonset }} are not scheduled or not ready

## PromQL 查询

```promql
(kube_daemonset_status_number_ready / kube_daemonset_status_desired_number_scheduled * 100 < 100 and kube_daemonset_status_desired_number_scheduled > 0) or kube_daemonset_status_desired_number_scheduled - kube_daemonset_status_current_number_scheduled > 0
```

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
