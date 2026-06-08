# Cilium agent API errors

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Cilium agent {{ $labels.pod }} API is returning 5xx errors ({{ $labels.return_code }}). Agent may be unhealthy.

## PromQL 查询

```promql
sum(rate(cilium_agent_api_process_time_seconds_count{return_code=~"5[0-9][0-9]"}[5m])) by (pod, return_code) > 0.05
```

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / Cilium
