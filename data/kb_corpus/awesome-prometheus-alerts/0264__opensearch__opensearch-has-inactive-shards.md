# OpenSearch has inactive shards

> Group: **Databases**  
> Service: **OpenSearch**  
> Exporter: `opensearch-project-opensearch-prometheus-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

OpenSearch cluster {{ $labels.cluster }} has inactive shards

## PromQL 查询

```promql
opensearch_cluster_shards_active_percent < 100.0
```

## 故障定位

- 触发该告警时, 检查 OpenSearch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / OpenSearch
