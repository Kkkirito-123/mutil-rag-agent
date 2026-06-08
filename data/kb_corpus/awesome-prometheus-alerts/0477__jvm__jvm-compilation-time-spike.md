# JVM compilation time spike

> Group: **Runtimes**  
> Service: **JVM**  
> Exporter: `jvm-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Excessive JIT compilation time consuming CPU

## PromQL 查询

```promql
rate(jvm_compilation_time_seconds_total[5m]) > 0.1
```

## 故障定位

- 触发该告警时, 检查 JVM 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / JVM
