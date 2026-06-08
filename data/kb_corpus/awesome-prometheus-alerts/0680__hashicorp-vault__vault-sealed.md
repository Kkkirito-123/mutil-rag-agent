# Vault sealed

> Group: **Network and security**  
> Service: **Hashicorp Vault**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Vault instance is sealed on {{ $labels.instance }}

## PromQL 查询

```promql
vault_core_unsealed == 0
```

## 故障定位

- 触发该告警时, 检查 Hashicorp Vault 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Network and security / Hashicorp Vault
