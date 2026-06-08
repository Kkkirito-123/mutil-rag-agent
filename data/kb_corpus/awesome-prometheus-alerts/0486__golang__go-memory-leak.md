# Go memory leak

> Group: **Runtimes**  
> Service: **Golang**  
> Exporter: `golang-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Go application has sustained high allocation rate (> 1GB/s), potential memory leak

## PromQL 查询

```promql
rate(go_memstats_alloc_bytes_total[5m]) > 1e9
```

## 故障定位

- 触发该告警时, 检查 Golang 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / Golang
