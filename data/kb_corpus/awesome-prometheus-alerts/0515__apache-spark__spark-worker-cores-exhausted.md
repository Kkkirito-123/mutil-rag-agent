# Spark worker cores exhausted

> Group: **Data engineering**  
> Service: **Apache Spark**  
> Exporter: `spark-prometheus`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Spark worker {{ $labels.instance }} has no free cores.

## PromQL 查询

```promql
metrics_worker_coresFree_Value == 0
```

## 处理建议 / Comments

Fires when a worker has no free cores. This may be normal under high load but can indicate capacity issues.

## 故障定位

- 触发该告警时, 检查 Apache Spark 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Apache Spark
