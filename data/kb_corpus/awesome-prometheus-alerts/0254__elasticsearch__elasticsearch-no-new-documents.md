# Elasticsearch no new documents

> Group: **Databases**  
> Service: **Elasticsearch**  
> Exporter: `prometheus-community-elasticsearch-exporter`  
> Severity: **warning**

## 现象 / Description

No new documents for 10 min!

## PromQL 查询

```promql
increase(elasticsearch_indices_indexing_index_total{es_data_node="true"}[10m]) < 1
```

## 故障定位

- 触发该告警时, 检查 Elasticsearch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Elasticsearch
