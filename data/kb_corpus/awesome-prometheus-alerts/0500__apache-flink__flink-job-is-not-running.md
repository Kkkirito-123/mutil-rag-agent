# Flink job is not running

> Group: **Data engineering**  
> Service: **Apache Flink**  
> Exporter: `flink-prometheus-reporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

No Flink jobs are currently running. All jobs may have failed or been cancelled.

## PromQL 查询

```promql
flink_jobmanager_numRunningJobs == 0
```

## 故障定位

- 触发该告警时, 检查 Apache Flink 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Data engineering / Apache Flink
