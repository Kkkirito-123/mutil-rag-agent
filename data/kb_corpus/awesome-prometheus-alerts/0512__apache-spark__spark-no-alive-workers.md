# Spark no alive workers

> Group: **Data engineering**  
> Service: **Apache Spark**  
> Exporter: `spark-prometheus`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

No Spark workers are alive. The cluster has no processing capacity.

## PromQL 查询

```promql
metrics_master_aliveWorkers_Value == 0
```

## 故障定位

- 触发该告警时, 检查 Apache Spark 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Data engineering / Apache Spark
