# Cilium agent endpoint create failure

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **info**  
> Duration (for): `5m`

## 现象 / Description

Cilium agent {{ $labels.pod }} is failing CNI endpoint-create calls. New pods may fail to get networking.

## PromQL 查询

```promql
sum(rate(cilium_api_limiter_processed_requests_total{api_call=~"endpoint-create", outcome="fail"}[1m])) by (pod, api_call) > 0.05
```

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Network and security / Cilium
