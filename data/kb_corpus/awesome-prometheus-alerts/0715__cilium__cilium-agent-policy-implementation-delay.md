# Cilium agent policy implementation delay

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Cilium agent {{ $labels.pod }} P99 policy deployment latency exceeds 60 seconds. Endpoints may run with stale policies.

## PromQL 查询

```promql
histogram_quantile(0.99, sum(rate(cilium_policy_implementation_delay_bucket[5m])) by (le, pod)) > 60
```

## 处理建议 / Comments

Threshold of 60s is a rough default. Adjust based on cluster size and policy complexity.

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / Cilium
