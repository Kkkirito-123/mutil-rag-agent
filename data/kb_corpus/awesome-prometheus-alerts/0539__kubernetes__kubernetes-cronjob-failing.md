# Kubernetes CronJob failing

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **critical**

## 现象 / Description

CronJob {{ $labels.namespace }}/{{ $labels.cronjob }} is failing

## PromQL 查询

```promql
(kube_cronjob_status_last_schedule_time > kube_cronjob_status_last_successful_time) AND (kube_cronjob_status_active == 0) AND (kube_cronjob_spec_suspend == 0)
```

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
