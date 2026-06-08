# Solr update errors

> Group: **Databases**  
> Service: **Solr**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Solr collection {{ $labels.collection }} has failed updates for replica {{ $labels.replica }} on {{ $labels.base_url }}.

## PromQL 查询

```promql
increase(solr_metrics_core_update_handler_errors_total[1m]) > 1
```

## 故障定位

- 触发该告警时, 检查 Solr 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Solr
