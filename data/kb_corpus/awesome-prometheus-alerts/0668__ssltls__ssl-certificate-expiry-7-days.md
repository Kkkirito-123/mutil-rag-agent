# SSL certificate expiry (< 7 days)

> Group: **Network and security**  
> Service: **SSL/TLS**  
> Exporter: `ribbybibby-ssl-exporter`  
> Severity: **warning**

## 现象 / Description

{{ $labels.instance }} Certificate is expiring in 7 days

## PromQL 查询

```promql
ssl_verified_cert_not_after{chain_no="0"} - time() < 86400 * 7
```

## 故障定位

- 触发该告警时, 检查 SSL/TLS 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / SSL/TLS
