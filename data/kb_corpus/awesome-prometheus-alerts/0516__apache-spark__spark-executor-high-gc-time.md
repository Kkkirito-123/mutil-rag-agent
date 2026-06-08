# Spark executor high GC time

> Group: **Data engineering**  
> Service: **Apache Spark**  
> Exporter: `spark-prometheus`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Spark executor {{ $labels.executor_id }} in {{ $labels.application_name }} is spending too much time in GC.

## PromQL 查询

```promql
metrics_executor_totalGCTime_seconds_total / metrics_executor_totalDuration > 0.1 and metrics_executor_totalDuration > 0
```

## 处理建议 / Comments

Fires when more than 10% of executor time is spent in garbage collection.
This metric comes from the PrometheusResource endpoint (/metrics/executors/prometheus/).

## 故障定位

- 触发该告警时, 检查 Apache Spark 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Apache Spark
