# Kubernetes API server errors

> Group: **Orchestrators**  
> Service: **Kubernetes**  
> Exporter: `kubestate-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Kubernetes API server is experiencing {{ $value | humanize }}% error rate

## PromQL 查询

```promql
sum(rate(apiserver_request_total{job="apiserver",code=~"(?:5..)"}[1m])) by (instance, job) / sum(rate(apiserver_request_total{job="apiserver"}[1m])) by (instance, job) * 100 > 3 and sum(rate(apiserver_request_total{job="apiserver"}[1m])) by (instance, job) > 0
```

## 故障定位

- 触发该告警时, 检查 Kubernetes 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Orchestrators / Kubernetes
