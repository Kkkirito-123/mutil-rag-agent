# Flink task high backpressure time

> Group: **Data engineering**  
> Service: **Apache Flink**  
> Exporter: `flink-prometheus-reporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Flink task {{ $labels.task_name }} is spending {{ $value | humanize }}ms/sec in backpressure.

## PromQL 查询

```promql
flink_taskmanager_job_task_backPressuredTimeMsPerSecond > 500
```

## 处理建议 / Comments

Fires when a task spends more than 500ms/sec backpressured. This indicates the task cannot keep up with upstream data rate.

## 故障定位

- 触发该告警时, 检查 Apache Flink 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Apache Flink
