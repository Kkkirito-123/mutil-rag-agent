# Meilisearch http response time

> Group: **Databases**  
> Service: **Meilisearch**  
> Exporter: `embedded-exporter`  
> Severity: **warning**

## 现象 / Description

Meilisearch http response time is too high

## PromQL 查询

```promql
meilisearch_http_response_time_seconds > 0.5
```

## 故障定位

- 触发该告警时, 检查 Meilisearch 的相关指标和日志
- 严重等级: warning
- 来源: awesome-prometheus-alerts / Databases / Meilisearch
