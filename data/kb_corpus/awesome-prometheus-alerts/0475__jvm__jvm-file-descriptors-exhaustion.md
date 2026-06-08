# JVM file descriptors exhaustion

> Group: **Runtimes**  
> Service: **JVM**  
> Exporter: `jvm-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

JVM process is running out of file descriptors (> 90% used)

## PromQL 查询

```promql
(process_open_fds / process_max_fds) * 100 > 90 and process_max_fds > 0
```

## 处理建议 / Comments

process_open_fds and process_max_fds are generic metrics from the Prometheus client library, not JVM-specific.
This alert will also fire for Go, Python, or any process exposing these metrics.

## 故障定位

- 触发该告警时, 检查 JVM 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / JVM
