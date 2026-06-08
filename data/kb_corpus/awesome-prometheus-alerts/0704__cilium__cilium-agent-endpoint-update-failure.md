# Cilium agent endpoint update failure

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Cilium agent {{ $labels.pod }} is failing K8s endpoint update API calls ({{ $labels.method }} {{ $labels.return_code }}).

## PromQL 查询

```promql
sum(rate(cilium_k8s_client_api_calls_total{method=~"(PUT|POST|PATCH)", endpoint="endpoint", return_code!~"2[0-9][0-9]"}[5m])) by (pod, method, return_code) > 0.05
```

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / Cilium
