# JVM threads deadlocked

> Group: **Runtimes**  
> Service: **JVM**  
> Exporter: `jvm-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

JVM has deadlocked threads

## PromQL 查询

```promql
jvm_threads_deadlocked > 0
```

## 故障定位

- 触发该告警时, 检查 JVM 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Runtimes / JVM
