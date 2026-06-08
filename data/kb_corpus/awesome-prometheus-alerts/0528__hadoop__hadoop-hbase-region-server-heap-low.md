# Hadoop HBase Region Server Heap Low

> Group: **Data engineering**  
> Service: **Hadoop**  
> Exporter: `jmx_exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

HBase Region Servers are running low on heap space.

## PromQL 查询

```promql
hadoop_hbase_region_server_heap_bytes / hadoop_hbase_region_server_max_heap_bytes > 0.8 and hadoop_hbase_region_server_max_heap_bytes > 0
```

## 故障定位

- 触发该告警时, 检查 Hadoop 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Hadoop
