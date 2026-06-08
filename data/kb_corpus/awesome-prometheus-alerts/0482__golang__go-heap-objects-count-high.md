# Go heap objects count high

> Group: **Runtimes**  
> Service: **Golang**  
> Exporter: `golang-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Go heap has too many live objects (> 10M), high GC pressure

## PromQL 查询

```promql
go_memstats_heap_objects > 10000000
```

## 处理建议 / Comments

Threshold is a rough default. Adjust based on your application's normal object count.

## 故障定位

- 触发该告警时, 检查 Golang 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / Golang
