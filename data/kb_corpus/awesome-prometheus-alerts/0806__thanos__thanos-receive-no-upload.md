# Thanos Receive No Upload

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-receiver`  
> Severity: **critical**  
> Duration (for): `3h`

## 现象 / Description

Thanos Receive {{$labels.instance}} has not uploaded latest data to object storage.

## PromQL 查询

```promql
(up{job=~".*thanos-receive.*"} - 1) + on (job, instance) (sum by (job, instance) (increase(thanos_shipper_uploads_total{job=~".*thanos-receive.*"}[3h])) == 0)
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Thanos
