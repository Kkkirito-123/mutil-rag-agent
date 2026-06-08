# Elasticsearch Healthy Nodes

> Group: **Databases**  
> Service: **Elasticsearch**  
> Exporter: `prometheus-community-elasticsearch-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Missing node in Elasticsearch cluster

## PromQL 查询

```promql
elasticsearch_cluster_health_number_of_nodes < 3
```

## 处理建议 / Comments

1m delay allows a restart without triggering an alert.

## 故障定位

- 触发该告警时, 检查 Elasticsearch 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Elasticsearch
