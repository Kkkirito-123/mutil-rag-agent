# Flink checkpoint duration high

> Group: **Data engineering**  
> Service: **Apache Flink**  
> Exporter: `flink-prometheus-reporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Flink job {{ $labels.job_name }} last checkpoint took {{ $value | humanizeDuration }} to complete.

## PromQL 查询

```promql
flink_jobmanager_job_lastCheckpointDuration / 1000 > 60
```

## 处理建议 / Comments

Value is converted from milliseconds to seconds for correct humanizeDuration display.
Threshold is 60 seconds. Adjust based on your checkpoint interval and state size.

## 故障定位

- 触发该告警时, 检查 Apache Flink 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Apache Flink
