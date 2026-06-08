# Solr replication errors

> Group: **Databases**  
> Service: **Solr**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Solr collection {{ $labels.collection }} has replication errors for replica {{ $labels.replica }} on {{ $labels.base_url }}.

## PromQL 查询

```promql
increase(solr_metrics_core_errors_total{category="REPLICATION"}[1m]) > 1
```

## 故障定位

- 触发该告警时, 检查 Solr 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Solr
