# Flink no TaskManagers registered

> Group: **Data engineering**  
> Service: **Apache Flink**  
> Exporter: `flink-prometheus-reporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

No TaskManagers are registered with the JobManager. The cluster has no processing capacity.

## PromQL 查询

```promql
flink_jobmanager_numRegisteredTaskManagers == 0
```

## 故障定位

- 触发该告警时, 检查 Apache Flink 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Data engineering / Apache Flink
