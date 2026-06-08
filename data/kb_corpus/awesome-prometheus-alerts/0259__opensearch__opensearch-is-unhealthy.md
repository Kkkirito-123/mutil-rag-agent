# OpenSearch is unhealthy

> Group: **Databases**  
> Service: **OpenSearch**  
> Exporter: `opensearch-project-opensearch-prometheus-exporter`  
> Severity: **critical**

## 现象 / Description

OpenSearch cluster {{ $labels.cluster }} is unhealthy

## PromQL 查询

```promql
opensearch_cluster_status != 0
```

## 故障定位

- 触发该告警时, 检查 OpenSearch 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / OpenSearch
