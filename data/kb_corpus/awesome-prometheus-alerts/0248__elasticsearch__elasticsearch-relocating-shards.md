# Elasticsearch relocating shards

> Group: **Databases**  
> Service: **Elasticsearch**  
> Exporter: `prometheus-community-elasticsearch-exporter`  
> Severity: **info**

## 现象 / Description

Elasticsearch is relocating shards

## PromQL 查询

```promql
elasticsearch_cluster_health_relocating_shards > 0
```

## 故障定位

- 触发该告警时, 检查 Elasticsearch 的相关指标和日志
- 严重等级: info
- 来源: awesome-prometheus-alerts / Databases / Elasticsearch
