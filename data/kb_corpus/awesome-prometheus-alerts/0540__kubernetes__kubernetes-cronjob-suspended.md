# Kubernetes CronJob suspended

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **warning**

## 现象 / Description

CronJob {{ $labels.namespace }}/{{ $labels.cronjob }} is suspended

## PromQL 查询

```promql
kube_cronjob_spec_suspend != 0
```

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
