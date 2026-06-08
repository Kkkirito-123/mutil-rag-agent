# Caddy high HTTP 4xx error rate service

> Group: **Proxies, load balancers and service meshes**  
> Service: **Caddy**  
> Exporter: `embedded-exporter`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Caddy service 4xx error rate is above 5%

## PromQL 查询

```promql
sum(rate(caddy_http_request_duration_seconds_count{code=~"4.."}[3m])) by (instance) / sum(rate(caddy_http_request_duration_seconds_count[3m])) by (instance) * 100 > 5 and sum(rate(caddy_http_request_duration_seconds_count[3m])) by (instance) > 0
```

## 故障定位

- 触发该告警时, 检查 Caddy 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Caddy
