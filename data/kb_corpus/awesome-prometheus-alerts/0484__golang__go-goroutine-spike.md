# Go goroutine spike

> Group: **Runtimes**  
> Service: **Golang**  
> Exporter: `golang-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Go goroutine count is growing rapidly ({{ $value | printf "%.0f" }} goroutines/s)

## PromQL 查询

```promql
deriv(go_goroutines[5m]) > 10
```

## 处理建议 / Comments

A threshold of 100/s only catches catastrophic leaks (30k goroutines in 5m). 10/s catches gradual leaks (~3k in 5m).
Adjust based on your application's expected concurrency patterns.

## 故障定位

- 触发该告警时, 检查 Golang 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / Golang
