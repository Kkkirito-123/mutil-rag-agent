# Go GC duration high

> Group: **Runtimes**  
> Service: **Golang**  
> Exporter: `golang-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Go GC pause duration is too high (max > 1s)

## PromQL 查询

```promql
go_gc_duration_seconds{quantile="1"} > 1
```

## 处理建议 / Comments

quantile="1" is the maximum observed GC pause in the current summary window, not p99.
A single outlier pause can push this above 1s. The for: 5m ensures the max stays elevated.

## 故障定位

- 触发该告警时, 检查 Golang 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / Golang
