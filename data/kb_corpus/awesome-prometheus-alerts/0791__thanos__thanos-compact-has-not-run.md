# Thanos Compact Has Not Run

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-compactor`  
> Severity: **warning**

## 现象 / Description

Thanos Compact {{$labels.job}} has not uploaded anything for 24 hours.

## PromQL 查询

```promql
(time() - max by (job) (max_over_time(thanos_objstore_bucket_last_successful_upload_time{job=~".*thanos-compact.*"}[24h]))) / 60 / 60 > 24
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Observability / Thanos
