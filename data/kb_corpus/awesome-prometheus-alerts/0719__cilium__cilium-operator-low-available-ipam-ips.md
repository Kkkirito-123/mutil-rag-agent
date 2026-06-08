# Cilium operator low available IPAM IPs

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Cilium operator IPAM IP pool is over 90% utilized. Allocate more IPs to avoid exhaustion.

## PromQL 查询

```promql
sum(cilium_operator_ipam_ips{type!="available"}) by () / sum(cilium_operator_ipam_ips) by () > 0.9 and sum(cilium_operator_ipam_ips) by () > 0
```

## 处理建议 / Comments

Threshold of 90% is a rough default. Adjust based on your pod churn rate and IP pool size.

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / Cilium
