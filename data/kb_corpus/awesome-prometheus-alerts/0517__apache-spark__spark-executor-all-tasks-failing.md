# Spark executor all tasks failing

> Group: **Data engineering**  
> Service: **Apache Spark**  
> Exporter: `spark-prometheus`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Spark executor {{ $labels.executor_id }} has only failing tasks ({{ $value }} failed, 0 completed).

## PromQL 查询

```promql
metrics_executor_failedTasks_total > 0 and metrics_executor_completedTasks_total == 0
```

## 故障定位

- 触发该告警时, 检查 Apache Spark 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Data engineering / Apache Spark
