# Go GC CPU fraction high

> Group: **Runtimes**  
> Service: **Golang**  
> Exporter: `golang-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Go GC is consuming too much CPU (> 5%)

## PromQL 查询

```promql
rate(go_gc_duration_seconds_sum[5m]) > 0.05
```

## 处理建议 / Comments

rate(go_gc_duration_seconds_sum) approximates the fraction of wall-clock time spent in GC.
This replaces go_memstats_gc_cpu_fraction which was removed in client_golang v1.12+.

## 故障定位

- 触发该告警时, 检查 Golang 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / Golang
