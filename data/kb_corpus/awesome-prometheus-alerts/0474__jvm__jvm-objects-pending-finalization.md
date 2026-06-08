# JVM objects pending finalization

> Group: **Runtimes**  
> Service: **JVM**  
> Exporter: `jvm-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

JVM has objects pending finalization, potential memory leak

## PromQL 查询

```promql
jvm_memory_objects_pending_finalization > 1000
```

## 故障定位

- 触发该告警时, 检查 JVM 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / JVM
