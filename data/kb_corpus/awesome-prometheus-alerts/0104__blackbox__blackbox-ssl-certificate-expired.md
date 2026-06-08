# Blackbox SSL certificate expired

> Group: **Basic resource monitoring**  
> Service: **Blackbox**  
> Exporter: `blackbox-exporter`  
> Severity: **critical**

## 现象 / Description

SSL certificate has expired already

## PromQL 查询

```promql
round((last_over_time(probe_ssl_earliest_cert_expiry[10m]) - time()) / 86400, 0.1) < 0
```

## 处理建议 / Comments

For probe_ssl_earliest_cert_expiry to be exposed after expiration, you
need to enable insecure_skip_verify. Note that this will disable
certificate validation.
See https://github.com/prometheus/blackbox_exporter/blob/master/CONFIGURATION.md#tls_config

## 故障定位

- 触发该告警时, 检查 Blackbox 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Blackbox
