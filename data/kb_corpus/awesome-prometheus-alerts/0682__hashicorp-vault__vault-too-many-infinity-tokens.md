# Vault too many infinity tokens

> Group: **Network and security**  
> Service: **Hashicorp Vault**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Too many non-expiring tokens on {{ $labels.instance }}: {{ $value }} tokens with infinite TTL.

## PromQL 查询

```promql
vault_token_count_by_ttl{creation_ttl="+Inf"} > 3
```

## 故障定位

- 触发该告警时, 检查 Hashicorp Vault 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / Hashicorp Vault
