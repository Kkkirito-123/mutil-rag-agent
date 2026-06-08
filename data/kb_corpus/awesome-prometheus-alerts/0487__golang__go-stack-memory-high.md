# Go stack memory high

> Group: **Runtimes**  
> Service: **Golang**  
> Exporter: `golang-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Go stack memory usage is high (> 1GB), likely excessive goroutines or deep recursion

## PromQL 查询

```promql
go_memstats_stack_inuse_bytes > 1e9
```

## 故障定位

- 触发该告警时, 检查 Golang 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / Golang
