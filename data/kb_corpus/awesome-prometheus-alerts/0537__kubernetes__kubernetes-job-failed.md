# Kubernetes Job failed

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **warning**

## 现象 / Description

Job {{ $labels.namespace }}/{{ $labels.job_name }} failed to complete

## PromQL 查询

```promql
kube_job_status_failed > 0
```

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
