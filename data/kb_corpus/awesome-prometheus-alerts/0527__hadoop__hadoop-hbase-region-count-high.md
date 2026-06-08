# Hadoop HBase Region Count High

> Group: **Data engineering**  
> Service: **Hadoop**  
> Exporter: `jmx_exporter`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

The HBase cluster has an unusually high number of regions.

## PromQL 查询

```promql
hadoop_hbase_region_count > 5000
```

## 故障定位

- 触发该告警时, 检查 Hadoop 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Hadoop
