# Elasticsearch pending tasks

> Group: **Databases**  
> Service: **Elasticsearch**  
> Exporter: `prometheus-community-elasticsearch-exporter`  
> Severity: **warning**  
> Duration (for): `15m`

## 现象 / Description

Elasticsearch has pending tasks. Cluster works slowly.

## PromQL 查询

```promql
elasticsearch_cluster_health_number_of_pending_tasks > 0
```

## 故障定位

- 触发该告警时, 检查 Elasticsearch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Elasticsearch
