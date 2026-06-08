# Cert-Manager certificate expiring soon

> Group: **Network and security**  
> Service: **cert-manager**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `1h`

## 现象 / Description

The certificate {{ $labels.name }} is expiring in less than 21 days.

## PromQL 查询

```promql
avg by (exported_namespace, namespace, name) (certmanager_certificate_expiration_timestamp_seconds - time()) < (21 * 24 * 3600)
```

## 处理建议 / Comments

Threshold of 21 days is a rough default. ACME certificates are typically renewed 30 days before expiry, so expiring within 21 days may indicate issuer misconfiguration.

## 故障定位

- 触发该告警时, 检查 cert-manager 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / cert-manager
