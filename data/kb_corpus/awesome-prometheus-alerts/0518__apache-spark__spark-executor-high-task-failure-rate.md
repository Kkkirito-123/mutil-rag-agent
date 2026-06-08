# Spark executor high task failure rate

> Group: **Data engineering**  
> Service: **Apache Spark**  
> Exporter: `spark-prometheus`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Spark executor {{ $labels.executor_id }} has a task failure rate above 10%.

## PromQL 查询

```promql
metrics_executor_failedTasks_total / metrics_executor_totalTasks_total > 0.1 and metrics_executor_totalTasks_total > 0
```

## 故障定位

- 触发该告警时, 检查 Apache Spark 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Apache Spark
