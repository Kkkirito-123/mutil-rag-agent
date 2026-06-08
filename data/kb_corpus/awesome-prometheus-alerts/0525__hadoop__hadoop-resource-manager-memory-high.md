# Hadoop Resource Manager Memory High

> Group: **Data engineering**  
> Service: **Hadoop**  
> Exporter: `jmx_exporter`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

The Hadoop ResourceManager is approaching its memory limit.

## PromQL 查询

```promql
hadoop_resourcemanager_memory_bytes / hadoop_resourcemanager_memory_max_bytes > 0.8 and hadoop_resourcemanager_memory_max_bytes > 0
```

## 故障定位

- 触发该告警时, 检查 Hadoop 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Hadoop
