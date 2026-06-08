# Go goroutine count high

> Group: **Runtimes**  
> Service: **Golang**  
> Exporter: `golang-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Go application has too many goroutines (> 1000), potential goroutine leak

## PromQL 查询

```promql
go_goroutines > 1000
```

## 处理建议 / Comments

Threshold is a rough default. High-concurrency servers may legitimately run thousands of goroutines. Adjust to match your baseline.

## 故障定位

- 触发该告警时, 检查 Golang 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / Golang
