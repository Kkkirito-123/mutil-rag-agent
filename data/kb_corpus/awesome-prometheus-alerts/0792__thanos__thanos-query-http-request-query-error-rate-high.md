# Thanos Query Http Request Query Error Rate High

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-query`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Thanos Query {{$labels.job}} is failing to handle {{$value | humanize}}% of "query" requests.

## PromQL 查询

```promql
(sum by (job) (rate(http_requests_total{code=~"5..", job=~".*thanos-query.*", handler="query"}[5m]))/  sum by (job) (rate(http_requests_total{job=~".*thanos-query.*", handler="query"}[5m]))) * 100 > 5 and sum by (job) (rate(http_requests_total{job=~".*thanos-query.*", handler="query"}[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Thanos
