# Solr query errors

> Group: **Databases**  
> Service: **Solr**  
> Exporter: `embedded-exporter`  
> Severity: **warning**  
> Duration (for): `5m`

## 现象 / Description

Solr has increased query errors in collection {{ $labels.collection }} for replica {{ $labels.replica }} on {{ $labels.base_url }}.

## PromQL 查询

```promql
increase(solr_metrics_core_errors_total{category="QUERY"}[1m]) > 1
```

## 故障定位

- 触发该告警时, 检查 Solr 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Solr
