# Go thread count high

> Group: **Runtimes**  
> Service: **Golang**  
> Exporter: `golang-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Go OS thread count is high (> 500), potential blocking syscall or CGo leak

## PromQL 查询

```promql
go_threads > 500
```

## 处理建议 / Comments

Threshold is workload-dependent. Applications with heavy CGo or blocking I/O may legitimately use more OS threads. Adjust to match your baseline.

## 故障定位

- 触发该告警时, 检查 Golang 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / Golang
