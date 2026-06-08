# Elasticsearch High Query Rate

> Group: **Databases**  
> Service: **Elasticsearch**  
> Exporter: `prometheus-community-elasticsearch-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

The query rate on Elasticsearch cluster is higher than the threshold.

## PromQL 查询

```promql
sum(rate(elasticsearch_indices_search_query_total[1m])) > 100
```

## 处理建议 / Comments

Threshold of 100 queries/s is very low for most production clusters. Adjust based on your expected query volume.

## 故障定位

- 触发该告警时, 检查 Elasticsearch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Elasticsearch
