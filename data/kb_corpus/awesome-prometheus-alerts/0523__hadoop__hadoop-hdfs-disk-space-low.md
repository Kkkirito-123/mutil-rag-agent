# Hadoop HDFS Disk Space Low

> Group: **Data engineering**  
> Service: **Hadoop**  
> Exporter: `jmx_exporter`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

Available HDFS disk space is running low.

## PromQL 查询

```promql
(hadoop_hdfs_bytes_total - hadoop_hdfs_bytes_used) / hadoop_hdfs_bytes_total < 0.1 and hadoop_hdfs_bytes_total > 0
```

## 故障定位

- 触发该告警时, 检查 Hadoop 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Hadoop
