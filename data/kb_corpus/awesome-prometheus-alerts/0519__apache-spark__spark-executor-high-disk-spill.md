# Spark executor high disk spill

> Group: **Data engineering**  
> Service: **Apache Spark**  
> Exporter: `spark-prometheus`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Spark executor {{ $labels.executor_id }} is spilling data to disk. Consider increasing executor memory.

## PromQL 查询

```promql
metrics_executor_diskUsed_bytes > 1e9
```

## 处理建议 / Comments

diskUsed is a gauge, not a counter — do not use rate(). Threshold of 1GB is a rough default.
Disk spilling indicates insufficient memory for the workload.

## 故障定位

- 触发该告警时, 检查 Apache Spark 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Apache Spark
