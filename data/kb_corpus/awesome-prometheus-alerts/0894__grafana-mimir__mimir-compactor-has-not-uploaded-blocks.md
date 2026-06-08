# Mimir compactor has not uploaded blocks

> Group: **Observability**  
> Service: **Grafana Mimir**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `15m`

## 现象 / Description

Mimir compactor {{ $labels.instance }} has not uploaded any block in the last 24 hours.

## PromQL 查询

```promql
(time() - thanos_objstore_bucket_last_successful_upload_time{component="compactor"} > 86400) and thanos_objstore_bucket_last_successful_upload_time{component="compactor"} > 0
```

## 故障定位

- 触发该告警时, 检查 Grafana Mimir 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Grafana Mimir
