# Go heap in-use growing

> Group: **Runtimes**  
> Service: **Golang**  
> Exporter: `golang-exporter`  
> Severity: **warning**

## 现象 / Description

Go heap in-use memory is growing steadily, potential memory leak or under-sized heap

## PromQL 查询

```promql
deriv(go_memstats_heap_inuse_bytes[10m]) > 1e7
```

## 处理建议 / Comments

Alerts when heap in-use grows by more than 10MB/s sustained over 10 minutes.
Adjust threshold based on your workload.

## 故障定位

- 触发该告警时, 检查 Golang 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / Golang
