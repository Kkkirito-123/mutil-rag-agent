# Cilium agent Kubernetes client errors

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **info**  
> Duration (for): `5m`

## 现象 / Description

Cilium agent {{ $labels.pod }} is receiving errors from K8s API for endpoint {{ $labels.endpoint }} ({{ $labels.return_code }}).

## PromQL 查询

```promql
sum(rate(cilium_k8s_client_api_calls_total{endpoint!="metrics", return_code!~"2[0-9][0-9]"}[5m])) by (pod, endpoint, return_code) > 0.05
```

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Network and security / Cilium
