# Elasticsearch unassigned shards

> Group: **Databases**  
> Service: **Elasticsearch**  
> Exporter: `prometheus-community-elasticsearch-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

Elasticsearch has unassigned shards

## PromQL 查询

```promql
elasticsearch_cluster_health_unassigned_shards > 0
```

## 故障定位

- 触发该告警时, 检查 Elasticsearch 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Elasticsearch
