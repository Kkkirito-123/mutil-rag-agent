# Traefik service down

> Group: **Proxies, load balancers and service meshes**  
> Service: **Traefik**  
> Exporter: `embedded-exporter-v2`  
> Severity: **critical**

## 现象 / Description

All Traefik services are down

## PromQL 查询

```promql
count(traefik_service_server_up) by (service) == 0
```

## 故障定位

- 触发该告警时, 检查 Traefik 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Traefik
