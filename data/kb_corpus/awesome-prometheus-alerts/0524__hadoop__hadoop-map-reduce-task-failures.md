# Hadoop Map Reduce Task Failures

> Group: **Data engineering**  
> Service: **Hadoop**  
> Exporter: `jmx_exporter`  
> Severity: **critical**  
> Duration (for): `10m`

## 现象 / Description

There is an unusually high number of MapReduce task failures.

## PromQL 查询

```promql
increase(hadoop_mapreduce_task_failures_total[1h]) > 100
```

## 故障定位

- 触发该告警时, 检查 Hadoop 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Data engineering / Hadoop
