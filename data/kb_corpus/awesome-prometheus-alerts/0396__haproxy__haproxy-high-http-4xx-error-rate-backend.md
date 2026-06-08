# HAProxy high HTTP 4xx error rate backend

> Group: **Proxies, load balancers and service meshes**  
> Service: **HaProxy**  
> Exporter: `embedded-exporter-v2`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Too many HTTP requests with status 4xx (> 5%) on backend {{ $labels.proxy }}

## PromQL 查询

```promql
((sum by (proxy) (rate(haproxy_server_http_responses_total{code="4xx"}[1m])) / sum by (proxy) (rate(haproxy_server_http_responses_total[1m]))) * 100) > 5 and sum by (proxy) (rate(haproxy_server_http_responses_total[1m])) > 0
```

## 故障定位

- 触发该告警时, 检查 HaProxy 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / HaProxy
