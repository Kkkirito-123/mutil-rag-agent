# JVM old gen GC frequency

> Group: **Runtimes**  
> Service: **JVM**  
> Exporter: `jvm-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Frequent old/major GC cycles, indicating memory pressure

## PromQL 查询

```promql
rate(jvm_gc_collection_seconds_count{gc=~".*old.*|.*major.*"}[5m]) > 0.3
```

## 处理建议 / Comments

This regex matches CMS, G1, and Parallel collector names. It will not match ZGC or Shenandoah cycle names.
Adjust the gc label filter if you use a different collector.

## 故障定位

- 触发该告警时, 检查 JVM 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Runtimes / JVM
