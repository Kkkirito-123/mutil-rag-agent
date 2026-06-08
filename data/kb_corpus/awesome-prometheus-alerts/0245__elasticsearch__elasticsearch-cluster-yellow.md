# Elasticsearch Cluster Yellow

> Group: **Databases**  
> Service: **Elasticsearch**  
> Exporter: `prometheus-community-elasticsearch-exporter`  
> Severity: **warning**

## 现象 / Description

Elastic Cluster Yellow status

## PromQL 查询

```promql
elasticsearch_cluster_health_status{color="yellow"} == 1
```

## 故障定位

- 触发该告警时, 检查 Elasticsearch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Elasticsearch
