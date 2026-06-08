# Vault too many pending tokens

> Group: **Network and security**  
> Service: **Hashicorp Vault**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Too many pending tokens on {{ $labels.instance }}: {{ $value }} tokens created but not yet stored.

## PromQL 查询

```promql
avg(vault_token_create_count - vault_token_store_count) > 0
```

## 故障定位

- 触发该告警时, 检查 Hashicorp Vault 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / Hashicorp Vault
