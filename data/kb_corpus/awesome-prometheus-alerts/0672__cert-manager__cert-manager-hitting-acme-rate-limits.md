# Cert-Manager hitting ACME rate limits

> Group: **Network and security**  
> Service: **cert-manager**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Cert-Manager is being rate-limited by the ACME provider. Certificate issuance and renewal may be blocked for up to a week.

## PromQL 查询

```promql
sum by (host) (rate(certmanager_acme_client_request_count{status="429"}[5m])) > 0
```

## 处理建议 / Comments

Metric renamed in cert-manager v1.19+ (dropped the http_ prefix): certmanager_acme_client_request_count.
For cert-manager < v1.19, use: certmanager_http_acme_client_request_count.

## 故障定位

- 触发该告警时, 检查 cert-manager 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Network and security / cert-manager
