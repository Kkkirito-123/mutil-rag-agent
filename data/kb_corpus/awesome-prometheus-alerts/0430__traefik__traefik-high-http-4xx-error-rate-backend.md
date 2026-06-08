# Traefik high HTTP 4xx error rate backend

> Group: **Proxies, load balancers and service meshes**  
> Service: **Traefik**  
> Exporter: `embedded-exporter-v1`  
> Severity: **critical**  
> Duration (for): `1m`

## 现象 / Description

Traefik backend 4xx error rate is above 5%

## PromQL 查询

```promql
sum(rate(traefik_backend_requests_total{code=~"4.*"}[3m])) by (backend) / sum(rate(traefik_backend_requests_total[3m])) by (backend) * 100 > 5 and sum(rate(traefik_backend_requests_total[3m])) by (backend) > 0
```

## 故障定位

- 触发该告警时, 检查 Traefik 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Traefik
