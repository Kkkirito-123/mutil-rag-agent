# Elasticsearch disk space low

> Group: **Databases**  
> Service: **Elasticsearch**  
> Exporter: `prometheus-community-elasticsearch-exporter`  
> Severity: **warning**  
> Duration (for): `2m`

## 现象 / Description

The disk usage is over 80%

## PromQL 查询

```promql
elasticsearch_filesystem_data_available_bytes / elasticsearch_filesystem_data_size_bytes * 100 < 20 and elasticsearch_filesystem_data_size_bytes > 0
```

## 故障定位

- 触发该告警时, 检查 Elasticsearch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Elasticsearch
