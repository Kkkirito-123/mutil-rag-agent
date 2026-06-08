# Vault cluster health

> Group: **Network and security**  
> Service: **Hashicorp Vault**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Vault cluster is not healthy: only {{ $value | humanizePercentage }} of nodes are active.

## PromQL 查询

```promql
sum(vault_core_active) / count(vault_core_active) <= 0.5 and count(vault_core_active) > 0
```

## 故障定位

- 触发该告警时, 检查 Hashicorp Vault 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Network and security / Hashicorp Vault
