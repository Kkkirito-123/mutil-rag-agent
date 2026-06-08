# Thanos Sidecar Bucket Operations Failed

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-sidecar`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Thanos Sidecar {{$labels.instance}} bucket operations are failing ({{ $value | humanize }}/s).

## PromQL 查询

```promql
sum by (job, instance) (rate(thanos_objstore_bucket_operation_failures_total{job=~".*thanos-sidecar.*"}[5m])) > 0.05
```

## 处理建议 / Comments

Threshold of 0.05/s avoids firing on transient single-event spikes.

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Thanos
