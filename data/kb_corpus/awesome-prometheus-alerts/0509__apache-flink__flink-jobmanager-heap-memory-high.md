# Flink JobManager heap memory high

> Group: **Data engineering**  
> Service: **Apache Flink**  
> Exporter: `flink-prometheus-reporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Flink JobManager {{ $labels.instance }} heap memory usage is above 90%.

## PromQL 查询

```promql
flink_jobmanager_Status_JVM_Memory_Heap_Used / flink_jobmanager_Status_JVM_Memory_Heap_Max > 0.9 and flink_jobmanager_Status_JVM_Memory_Heap_Max > 0
```

## 故障定位

- 触发该告警时, 检查 Apache Flink 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Apache Flink
