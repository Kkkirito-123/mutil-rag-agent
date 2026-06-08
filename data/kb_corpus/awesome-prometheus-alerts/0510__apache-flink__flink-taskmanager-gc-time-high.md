# Flink TaskManager GC time high

> Group: **Data engineering**  
> Service: **Apache Flink**  
> Exporter: `flink-prometheus-reporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Flink TaskManager {{ $labels.instance }} is spending more than 10% of time in garbage collection.

## PromQL 查询

```promql
deriv(flink_taskmanager_Status_JVM_GarbageCollector_All_Time[5m]) > 100
```

## 处理建议 / Comments

Flink exposes GC time as a gauge (cumulative milliseconds), so deriv() is used instead of rate().
Threshold: more than 100ms/sec of GC time (10% of wall clock). Adjust based on your workload.

## 故障定位

- 触发该告警时, 检查 Apache Flink 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Apache Flink
