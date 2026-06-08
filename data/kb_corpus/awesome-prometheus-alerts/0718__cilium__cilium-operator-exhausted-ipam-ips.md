# Cilium operator exhausted IPAM IPs

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Cilium operator has no available IPAM IPs. New pods will fail to schedule networking.

## PromQL 查询

```promql
sum(cilium_operator_ipam_ips{type="available"}) by () <= 0
```

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Network and security / Cilium
