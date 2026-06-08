# Hadoop YARN Container Allocation Failures

> Group: **Data engineering**  
> Service: **Hadoop**  
> Exporter: `jmx_exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

There is a significant number of YARN container allocation failures.

## PromQL 查询

```promql
increase(hadoop_yarn_container_allocation_failures_total[1h]) > 10
```

## 故障定位

- 触发该告警时, 检查 Hadoop 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Hadoop
