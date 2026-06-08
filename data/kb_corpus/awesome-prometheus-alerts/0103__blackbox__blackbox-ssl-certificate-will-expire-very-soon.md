# Blackbox SSL certificate will expire very soon

> Group: **Basic resource monitoring**  
> Service: **Blackbox**  
> Exporter: `blackbox-exporter`  
> Severity: **critical**

## 现象 / Description

SSL certificate expires in less than 3 days

## PromQL 查询

```promql
0 <= round((last_over_time(probe_ssl_earliest_cert_expiry[10m]) - time()) / 86400, 0.1) < 3
```

## 故障定位

- 触发该告警时, 检查 Blackbox 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Blackbox
