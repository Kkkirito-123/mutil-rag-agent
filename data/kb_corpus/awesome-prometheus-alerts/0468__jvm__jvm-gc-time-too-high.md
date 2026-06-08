# JVM GC time too high

> Group: **Runtimes**  
> Service: **JVM**  
> Exporter: `jvm-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

JVM is spending too much time in garbage collection (> 5% of wall clock time)

## PromQL 查询

```promql
sum by (instance)(rate(jvm_gc_collection_seconds_sum[5m])) > 0.05
```

## 故障定位

- 触发该告警时, 检查 JVM 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / JVM
