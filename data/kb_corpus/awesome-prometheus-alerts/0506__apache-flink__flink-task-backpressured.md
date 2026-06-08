# Flink task backpressured

> Group: **Data engineering**  
> Service: **Apache Flink**  
> Exporter: `flink-prometheus-reporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Flink task {{ $labels.task_name }} in job {{ $labels.job_name }} is backpressured.

## PromQL 查询

```promql
flink_taskmanager_job_task_isBackPressured == 1
```

## 故障定位

- 触发该告警时, 检查 Apache Flink 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Apache Flink
