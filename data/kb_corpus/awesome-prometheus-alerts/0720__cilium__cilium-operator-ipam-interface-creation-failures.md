# Cilium operator IPAM interface creation failures

> Group: **Network and security**  
> Service: **Cilium**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

Cilium operator is failing to create IPAM network interfaces. IP allocation may be impacted.

## PromQL 查询

```promql
sum(rate(cilium_operator_ipam_interface_creation_ops{status!="success"}[5m])) by () > 0.05
```

## 处理建议 / Comments

Some Cilium versions may not have a status label on this metric. Verify against your Cilium version.

## 故障定位

- 触发该告警时, 检查 Cilium 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / Cilium
