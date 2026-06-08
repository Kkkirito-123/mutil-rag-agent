# Flink TaskManager heap memory high

> Group: **Data engineering**  
> Service: **Apache Flink**  
> Exporter: `flink-prometheus-reporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Flink TaskManager {{ $labels.instance }} heap memory usage is above 90%.

## PromQL 查询

```promql
flink_taskmanager_Status_JVM_Memory_Heap_Used / flink_taskmanager_Status_JVM_Memory_Heap_Max > 0.9 and flink_taskmanager_Status_JVM_Memory_Heap_Max > 0
```

## 处理建议 / Comments

Flink TaskManagers manage their own memory pool. High JVM heap usage (outside managed memory) may indicate memory leaks or misconfiguration.

## 故障定位

- 触发该告警时, 检查 Apache Flink 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Apache Flink
