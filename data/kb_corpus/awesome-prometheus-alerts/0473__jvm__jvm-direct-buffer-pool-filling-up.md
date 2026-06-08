# JVM direct buffer pool filling up

> Group: **Runtimes**  
> Service: **JVM**  
> Exporter: `jvm-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

JVM direct buffer pool is filling up (> 90%)

## PromQL 查询

```promql
(jvm_buffer_pool_used_bytes / jvm_buffer_pool_capacity_bytes) * 100 > 90 and jvm_buffer_pool_capacity_bytes > 0
```

## 故障定位

- 触发该告警时, 检查 JVM 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / JVM
