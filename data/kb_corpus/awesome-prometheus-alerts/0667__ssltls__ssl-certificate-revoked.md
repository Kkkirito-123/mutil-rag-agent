# SSL certificate revoked

> Group: **Network and security**  
> Service: **SSL/TLS**  
> Exporter: `ribbybibby-ssl-exporter`  
> Severity: **critical**

## 现象 / Description

SSL certificate revoked {{ $labels.instance }}

## PromQL 查询

```promql
ssl_ocsp_response_status == 1
```

## 故障定位

- 触发该告警时, 检查 SSL/TLS 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Network and security / SSL/TLS
