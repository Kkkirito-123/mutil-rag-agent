# Elasticsearch Cluster Red

> Group: **Databases**  
> Service: **Elasticsearch**  
> Exporter: `prometheus-community-elasticsearch-exporter`  
> Severity: **critical**

## 现象 / Description

Elastic Cluster Red status

## PromQL 查询

```promql
elasticsearch_cluster_health_status{color="red"} == 1
```

## 故障定位

- 触发该告警时, 检查 Elasticsearch 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Databases / Elasticsearch
