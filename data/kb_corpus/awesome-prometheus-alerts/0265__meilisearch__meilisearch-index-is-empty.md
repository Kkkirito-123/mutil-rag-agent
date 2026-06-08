# Meilisearch index is empty

> Group: **Databases**  
> Service: **Meilisearch**  
> Exporter: `embedded-exporter`  
> Severity: **warning**

## 现象 / Description

Meilisearch index {{ $labels.index }} has zero documents

## PromQL 查询

```promql
meilisearch_index_docs_count == 0
```

## 故障定位

- 触发该告警时, 检查 Meilisearch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Meilisearch
