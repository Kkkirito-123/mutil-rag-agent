# Istio Kubernetes gateway availability drop

> Group: **Proxies, load balancers and service meshes**  
> Service: **Istio**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `1m`

## 现象 / Description

Istio ingress gateway has only {{ $value }} available pod(s). Inbound traffic will likely be affected.

## PromQL 查询

```promql
min(kube_deployment_status_replicas_available{deployment="istio-ingressgateway", namespace="istio-system"}) without (instance, pod) < 2
```

## 故障定位

- 触发该告警时, 检查 Istio 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Istio
