# Traefik backend down

> Group: **Proxies, load balancers and service meshes**  
> Service: **Traefik**  
> Exporter: `embedded-exporter-v1`  
> Severity: **critical**

## 现象 / Description

All Traefik backends are down

## PromQL 查询

```promql
count(traefik_backend_server_up) by (backend) == 0
```

## 故障定位

- 触发该告警时, 检查 Traefik 的相关指标和日志
- 严重等级: critical
- 来源: awesome-prometheus-alerts / Proxies, load balancers and service meshes / Traefik
