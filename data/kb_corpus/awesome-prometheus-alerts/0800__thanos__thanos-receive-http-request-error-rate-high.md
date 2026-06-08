# Thanos Receive Http Request Error Rate High

> Group: **Observability**  
> Service: **Thanos**  
> Exporter: `thanos-receiver`  
> Severity: **critical**  
> Duration (for): `5m`

## 现象 / Description

Thanos Receive {{$labels.job}} is failing to handle {{$value | humanize}}% of requests.

## PromQL 查询

```promql
(sum by (job) (rate(http_requests_total{code=~"5..", job=~".*thanos-receive.*", handler="receive"}[5m]))/  sum by (job) (rate(http_requests_total{job=~".*thanos-receive.*", handler="receive"}[5m]))) * 100 > 5 and sum by (job) (rate(http_requests_total{job=~".*thanos-receive.*", handler="receive"}[5m])) > 0
```

## 故障定位

- 触发该告警时, 检查 Thanos 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Observability / Thanos
