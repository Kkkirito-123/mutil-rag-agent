# SSL certificate OCSP status unknown

> Group: **Network and security**  
> Service: **SSL/TLS**  
> Exporter: `ribbybibby-ssl-exporter`  
> Severity: **warning**

## 现象 / Description

Failed to get the OCSP status for {{ $labels.instance }}

## PromQL 查询

```promql
ssl_ocsp_response_status == 2
```

## 故障定位

- 触发该告警时, 检查 SSL/TLS 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Network and security / SSL/TLS
