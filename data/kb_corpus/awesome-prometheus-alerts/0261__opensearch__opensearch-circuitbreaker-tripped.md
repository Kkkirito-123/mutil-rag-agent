# OpenSearch circuitbreaker tripped

> Group: **Databases**  
> Service: **OpenSearch**  
> Exporter: `opensearch-project-opensearch-prometheus-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

The circuitbreaker on OpenSearch cluster {{ $labels.cluster }} has tripped to prevent Java OutOfMemoryError

## PromQL 查询

```promql
opensearch_circuitbreaker_tripped_count > 0
```

## 故障定位

- 触发该告警时, 检查 OpenSearch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / OpenSearch
