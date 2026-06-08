# Kubernetes CronJob too long

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **warning**

## 现象 / Description

CronJob {{ $labels.namespace }}/{{ $labels.cronjob }} is taking more than 1h to complete.

## PromQL 查询

```promql
kube_job_status_start_time > 0 and absent(kube_job_status_completion_time) and (time() - kube_job_status_start_time) > 3600
```

## 处理建议 / Comments

Threshold should be customized for each cronjob name.

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
