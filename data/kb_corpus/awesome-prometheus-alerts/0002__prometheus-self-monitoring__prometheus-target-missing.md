# Prometheus target missing

> Group: **Basic resource monitoring**  
> Service: **Prometheus self-monitoring**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

A Prometheus target has disappeared. An exporter might be crashed.

## PromQL 查询

```promql
up == 0 unless on(job) (sum by (job) (up) == 0)
```

## 处理建议 / Comments

Only fire if at least one target in the job is still up.
If all targets are down, PrometheusJobMissing or PrometheusAllTargetsMissing will fire instead.

## 故障定位

- 触发该告警时, 检查 Prometheus self-monitoring 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Basic resource monitoring / Prometheus self-monitoring
