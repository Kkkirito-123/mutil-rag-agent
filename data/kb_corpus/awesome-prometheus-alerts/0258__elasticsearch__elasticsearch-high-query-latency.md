# Elasticsearch High Query Latency

> Group: **Databases**  
> Service: **Elasticsearch**  
> Exporter: `prometheus-community-elasticsearch-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

The query latency on Elasticsearch cluster is higher than the threshold (current value: {{ $value }}s).

## PromQL 查询

```promql
rate(elasticsearch_indices_search_query_time_seconds[1m]) / rate(elasticsearch_indices_search_query_total[1m]) > 1 and rate(elasticsearch_indices_search_query_total[1m]) > 0
```

## 故障定位

- 触发该告警时, 检查 Elasticsearch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Elasticsearch
