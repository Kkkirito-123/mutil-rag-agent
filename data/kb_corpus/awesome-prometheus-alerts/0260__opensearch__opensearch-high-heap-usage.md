# OpenSearch high heap usage

> Group: **Databases**  
> Service: **OpenSearch**  
> Exporter: `opensearch-project-opensearch-prometheus-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

OpenSearch heap usage on cluster {{ $labels.cluster }} is too high

## PromQL 查询

```promql
opensearch_jvm_mem_heap_used_percent > 90
```

## 故障定位

- 触发该告警时, 检查 OpenSearch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / OpenSearch
