# Flink no records processed

> Group: **Data engineering**  
> Service: **Apache Flink**  
> Exporter: `flink-prometheus-reporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Flink task {{ $labels.task_name }} has not processed any records in the last 5 minutes.

## PromQL 查询

```promql
delta(flink_taskmanager_job_task_numRecordsIn[5m]) == 0 and flink_taskmanager_job_task_numRecordsIn > 0
```

## 处理建议 / Comments

Only fires for tasks that have previously received records, to avoid false positives during startup.

## 故障定位

- 触发该告警时, 检查 Apache Flink 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Apache Flink
