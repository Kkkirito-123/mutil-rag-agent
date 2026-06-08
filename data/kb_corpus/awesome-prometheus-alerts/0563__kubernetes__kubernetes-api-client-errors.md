# Kubernetes API client errors

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Kubernetes API client is experiencing {{ $value | humanize }}% error rate

## PromQL 查询

```promql
(sum(rate(rest_client_requests_total{code=~"(4|5).."}[1m])) by (instance, job) / sum(rate(rest_client_requests_total[1m])) by (instance, job)) * 100 > 1 and sum(rate(rest_client_requests_total[1m])) by (instance, job) > 0
```

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
