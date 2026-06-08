# Hadoop Data Node Out Of Service

> Group: **Data engineering**  
> Service: **Hadoop**  
> Exporter: `jmx_exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

The Hadoop DataNode is not sending heartbeats.

## PromQL 查询

```promql
hadoop_datanode_last_heartbeat == 0
```

## 故障定位

- 触发该告警时, 检查 Hadoop 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Hadoop
