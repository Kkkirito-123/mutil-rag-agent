# Blackbox probe HTTP failure

> Group: **Basic resource monitoring**  
> Service: **Blackbox**  
> Exporter: `blackbox-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

HTTP status code is not 200-399

## PromQL 查询

```promql
probe_http_status_code <= 199 OR probe_http_status_code >= 400
```

## 故障定位

- 触发该告警时, 检查 Blackbox 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Blackbox
