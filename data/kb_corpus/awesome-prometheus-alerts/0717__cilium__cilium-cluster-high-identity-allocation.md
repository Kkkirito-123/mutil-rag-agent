# Cilium cluster high identity allocation

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Cilium cluster-wide identity allocation is above 80%. Approaching the maximum identity limit.

## PromQL 查询

```promql
(sum(cilium_identity{type="cluster_local"}) by () / (2^16-256)) > 0.8
```

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / Cilium
