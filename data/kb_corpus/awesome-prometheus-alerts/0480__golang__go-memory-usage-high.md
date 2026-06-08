# Go memory usage high

> Group: **Runtimes**  
> Service: **Golang**  
> Exporter: `golang-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Go heap allocation is using most of the runtime's reserved memory (> 90%), indicating the process may need more memory or has a leak

## PromQL 查询

```promql
(go_memstats_heap_alloc_bytes / go_memstats_sys_bytes) * 100 > 90
```

## 处理建议 / Comments

go_memstats_sys_bytes is the total memory obtained from the OS by the Go runtime, not total host memory.
This ratio measures Go-internal memory utilization, not system-level memory pressure.

## 故障定位

- 触发该告警时, 检查 Golang 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / Golang
