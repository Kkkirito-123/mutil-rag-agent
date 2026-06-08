# Pulsar topic very large backlog storage size

> Group: **Message brokers**  
> Service: **Pulsar**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `1h`

## 现象 / Description

The topic backlog storage size is over 20 GB

## PromQL 查询

```promql
sum(pulsar_storage_size) by (topic) > 20*1024*1024*1024
```

## 故障定位

- 触发该告警时, 检查 Pulsar 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Message brokers / Pulsar
