# Hadoop HBase Write Requests Latency High

> Group: **Data engineering**  
> Service: **Hadoop**  
> Exporter: `jmx_exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

HBase Write Requests are experiencing high latency.

## PromQL 查询

```promql
hadoop_hbase_write_requests_latency_seconds > 0.5
```

## 故障定位

- 触发该告警时, 检查 Hadoop 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Data engineering / Hadoop
