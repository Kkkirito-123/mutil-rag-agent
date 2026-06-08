# Solr low live node count

> Group: **Databases**  
> Service: **Solr**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Solr collection {{ $labels.collection }} has less than two live nodes for replica {{ $labels.replica }} on {{ $labels.base_url }}.

## PromQL 查询

```promql
solr_collections_live_nodes < 2
```

## 故障定位

- 触发该告警时, 检查 Solr 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Solr
