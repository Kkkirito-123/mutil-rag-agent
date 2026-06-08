# Caddy Reverse Proxy Down

> Group: **Proxies, load balancers and service meshes**  
> Service: **Caddy**  
> Exporter: `embedded-exporter`  
> Severity: **critical**

## 现象 / Description

Caddy reverse proxy upstream {{ $labels.upstream }} is unhealthy

## PromQL 查询

```promql
caddy_reverse_proxy_upstreams_healthy == 0
```

## 故障定位

- 触发该告警时, 检查 Caddy 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Caddy
