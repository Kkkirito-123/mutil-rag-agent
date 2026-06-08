# Kubernetes Job slow completion

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **critical**  
> Duration (for): `12h`

## 现象 / Description

Kubernetes Job {{ $labels.namespace }}/{{ $labels.job_name }} did not complete in time.

## PromQL 查询

```promql
kube_job_spec_completions - kube_job_status_succeeded - kube_job_status_failed > 0
```

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
