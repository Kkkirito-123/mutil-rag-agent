# Spark too many waiting apps

> Group: **Data engineering**  
> Service: **Apache Spark**  
> Exporter: `spark-prometheus`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Spark has {{ $value }} applications waiting for resources.

## PromQL 查询

```promql
metrics_master_waitingApps_Value > 10
```

## 处理建议 / Comments

Adjust the threshold based on your cluster's typical queuing behavior.

## 故障定位

- 触发该告警时, 检查 Apache Spark 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Apache Spark
