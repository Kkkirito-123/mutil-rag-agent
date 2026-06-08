# Kubernetes pod crash looping

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Pod {{ $labels.namespace }}/{{ $labels.pod }} is crash looping

## PromQL 查询

```promql
increase(kube_pod_container_status_restarts_total[1m]) > 3
```

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
