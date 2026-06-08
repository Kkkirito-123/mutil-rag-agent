# Spark worker memory exhausted

> Group: **Data engineering**  
> Service: **Apache Spark**  
> Exporter: `spark-prometheus`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

Spark worker {{ $labels.instance }} has no free memory ({{ $value }}MB free).

## PromQL 查询

```promql
metrics_worker_memFree_MB_Value == 0
```

## 故障定位

- 触发该告警时, 检查 Apache Spark 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Apache Spark
