# Elasticsearch High Indexing Rate

> Group: **Databases**  
> Service: **Elasticsearch**  
> Exporter: `prometheus-community-elasticsearch-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

The indexing rate on Elasticsearch cluster is higher than the threshold.

## PromQL 查询

```promql
sum(rate(elasticsearch_indices_indexing_index_total[1m]))> 10000
```

## 处理建议 / Comments

Threshold of 10000 ops/s is a rough default. Adjust based on your cluster capacity and expected workload.

## 故障定位

- 触发该告警时, 检查 Elasticsearch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Elasticsearch
