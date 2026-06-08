# Kubernetes PersistentVolume error

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **critical**

## 现象 / Description

Persistent volume {{ $labels.persistentvolume }} is in bad state

## PromQL 查询

```promql
kube_persistentvolume_status_phase{phase=~"Failed|Pending"} > 0
```

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
