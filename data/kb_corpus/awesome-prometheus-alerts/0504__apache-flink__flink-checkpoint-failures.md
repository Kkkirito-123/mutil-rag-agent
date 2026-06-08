# Flink checkpoint failures

> Group: **Data engineering**  
> Service: **Apache Flink**  
> Exporter: `flink-prometheus-reporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Flink job {{ $labels.job_name }} has {{ $value }} failed checkpoints in the last 10 minutes.

## PromQL 查询

```promql
delta(flink_jobmanager_job_numberOfFailedCheckpoints[10m]) > 1
```

## 故障定位

- 触发该告警时, 检查 Apache Flink 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Apache Flink
