# JVM threads BLOCKED

> Group: **Runtimes**  
> Service: **JVM**  
> Exporter: `jvm-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

JVM has high number of BLOCKED threads, indicating lock contention

## PromQL 查询

```promql
jvm_threads_state{state="BLOCKED"} > 50
```

## 故障定位

- 触发该告警时, 检查 JVM 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / JVM
