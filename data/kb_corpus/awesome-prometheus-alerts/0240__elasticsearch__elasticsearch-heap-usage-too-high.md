# Elasticsearch Heap Usage Too High

> Group: **Databases**  
> Service: **Elasticsearch**  
> Exporter: `prometheus-community-elasticsearch-exporter`  
> Severity: **critical**  
> Duration (for): `2m`

## 现象 / Description

The heap usage is over 90%

## PromQL 查询

```promql
(elasticsearch_jvm_memory_used_bytes{area="heap"} / elasticsearch_jvm_memory_max_bytes{area="heap"}) * 100 > 90 and elasticsearch_jvm_memory_max_bytes{area="heap"} > 0
```

## 故障定位

- 触发该告警时, 检查 Elasticsearch 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Elasticsearch
