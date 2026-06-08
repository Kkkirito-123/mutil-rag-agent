# Elasticsearch High Indexing Latency

> Group: **Databases**  
> Service: **Elasticsearch**  
> Exporter: `prometheus-community-elasticsearch-exporter`  
> Severity: **warning**  
> Duration (for): `10m`

## 现象 / Description

The indexing latency on Elasticsearch cluster is higher than the threshold (current value: {{ $value }}s).

## PromQL 查询

```promql
rate(elasticsearch_indices_indexing_index_time_seconds_total[5m]) / rate(elasticsearch_indices_indexing_index_total[5m]) > 0.01 and rate(elasticsearch_indices_indexing_index_total[5m]) > 0
```

## 处理建议 / Comments

Threshold of 10ms (0.01s) per indexing operation is a rough default. Adjust based on your document size and cluster performance.

## 故障定位

- 触发该告警时, 检查 Elasticsearch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Elasticsearch
